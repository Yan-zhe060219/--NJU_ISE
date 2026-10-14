"""本地学习记录工具，仅使用标准库。agent 用 JSON 请求调用，用户无需记命令。"""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import uuid
from urllib.parse import quote

TZ = timezone(timedelta(hours=8))
ROOT = Path(__file__).resolve().parent.parent
KINDS = {"studied", "self_report", "understanding", "mastery", "question", "mistake", "resolved", "skip_test", "checkpoint", "task_progress", "note"}
EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".md", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a", ".mp4", ".epub", ".csv", ".xlsx"}


def now():
    return datetime.now(TZ).isoformat(timespec="microseconds")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", value):
        raise ValueError("ID 只能含小写字母、数字、短横线、下划线，最多80字符")
    if value.split('.')[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("不能使用系统保留名称")
    return value


def inside(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or path == base.resolve():
        raise ValueError("路径必须在指定目录内")
    return path


def folder_name(value):
    """允许可读中文目录名，拒绝路径、Windows保留名及会被规范化的尾字符。"""
    if not isinstance(value, str) or not value.strip() or value in {".", ".."} or value != value.strip() or value.endswith(".") or re.search(r'[<>:"/\\|?*\x00-\x1f]', value):
        raise ValueError("目录名不能为空、路径或含系统禁用字符")
    if value.split('.')[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("不能使用系统保留名称")
    return value


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 临时文件与目标同目录；断电时保留未完成文件，不把半份 JSON 当记录。
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent, prefix=".write-", suffix=".tmp", delete=False) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
        temp = f.name
    os.replace(temp, path)


def write(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def lock(path):
    """操作系统锁随进程退出释放；不靠删除锁文件解锁。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("文件正在被另一对话更新，请重读后重试") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


class Learning:
    def __init__(self, root=ROOT):
        self.root = Path(os.path.abspath(root)).resolve()
        self.home = self.root / "learning"

    def goal(self, goal_id):
        identifier(goal_id)
        paths = [p.parent for p in self.goal_files() if read(p)["id"] == goal_id]
        if not paths:
            raise ValueError("学习目标不存在，请先创建入口")
        return paths[0]

    def goal_files(self):
        """只扫描目标身份文件，不扫描材料；兼容旧布局但不产生第二份身份。"""
        paths = []
        seen = set()
        for pattern in ("courses/*/*/goal.json", "papers/*/goal.json", "self-study/*/goal.json", "learning/goals/*/goal.json"):
            for file in sorted(self.root.glob(pattern)):
                if not file.resolve().is_relative_to(self.root):
                    raise ValueError("目标目录不能链接到工作区外")
                goal_id = identifier(read(file)["id"])
                if goal_id in seen:
                    raise ValueError("目标ID重复，请先核对目录，不能猜测使用哪一份")
                seen.add(goal_id)
                paths.append(file)
        return paths

    def records_snapshot(self):
        return sorted((str(p), sha(p)) for g in self.goal_files() for p in (g.parent / "records").glob("*.json"))

    def create(self, goal_id, title, kind, details=None, directory_name=None):
        identifier(goal_id)
        if kind not in {"course", "paper", "self-study", "exam"} or not str(title).strip():
            raise ValueError("需要目标名称及 course/paper/self-study/exam 类型")
        details = dict(details or {})
        name = folder_name(directory_name if directory_name is not None else title)
        if kind == "course":
            semester = details.get("semester")
            if not semester:
                raise ValueError("创建课程需要用户明确的学期 details.semester")
            base = inside(self.root / "courses", folder_name(semester))
        else:
            base = self.root / ("papers" if kind == "paper" else "self-study")
        path = inside(base, name)
        if not path.is_relative_to(self.root):
            raise ValueError("目标目录不能链接到工作区外")
        with lock(self.home / ".goals.lock"):
            if any(read(p)["id"] == goal_id for p in self.goal_files()) or path.exists():
                raise ValueError("目标ID或目录已存在，拒绝覆盖；已有课程应按迁移流程登记")
            parts = ["materials", "notes", "records", "sessions", "pending"]
            for part in parts:
                (path / part).mkdir(parents=True, exist_ok=True)
                atomic_text(path / part / ".gitkeep", "")
            write(path / "goal.json", {"schema": 1, "id": goal_id, "title": title, "kind": kind, "status": "awaiting_materials", "created": now(), "details": details or {}})
            write(path / "materials.json", {"schema": 1, "revision": 0, "items": []})
            atomic_text(path / "MAP.md", f"# {title}学习地图\n\n[学习对象入口](README.md) · [资料清单](MATERIALS.md) · [笔记](notes/)\n\n资料放入 `materials/` 后即可提问。当前没有已登记材料或正式笔记。\n\n## 疑问与薄弱点\n\n按需链接 records 中的记录；无证据不判断能力。\n")
            atomic_text(path / "README.md", f"# {title}\n\n[原始资料](materials/) · [资料清单](MATERIALS.md) · [正式笔记](notes/) · [学习地图](MAP.md)\n\n课件、教材、作业、试卷等原始文件都直接放入 `materials/`，无需先选类别。\n\n`records/` 保存学习事件，`sessions/` 保存续接点，`pending/` 保存待核实内容；由 agent 管理。\n\n目标ID：`{goal_id}`。导入不等于学过。\n")
            self.write_materials_manifest(path, read(path / "materials.json"))
        self.refresh_navigation()
        return {"goal": goal_id, "materials": str(path / "materials")}

    def adopt_course(self, goal_id, title, semester, directory_name=None, details=None):
        """给已有课程目录补齐学习入口，不移动或覆盖其中的文件。"""
        identifier(goal_id)
        if not str(title).strip() or not semester:
            raise ValueError("登记已有课程需要课程名称和明确学期")
        semester = folder_name(semester)
        name = folder_name(directory_name if directory_name is not None else title)
        path = inside(self.root / "courses" / semester, name)
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("目标目录不能链接到工作区外")
        with lock(self.home / ".goals.lock"):
            if any(read(p)["id"] == goal_id for p in self.goal_files()):
                raise ValueError("目标ID已存在，拒绝重复登记")
            if not path.is_dir() or (path / "goal.json").exists():
                raise ValueError("已有课程目录不存在或已经登记，拒绝覆盖")
            for part in ("materials", "notes", "records", "sessions", "pending"):
                folder = path / part
                folder.mkdir(parents=True, exist_ok=True)
                if not any(folder.iterdir()):
                    atomic_text(folder / ".gitkeep", "")
            goal = {"schema": 1, "id": goal_id, "title": title, "kind": "course", "status": "awaiting_materials", "created": now(), "details": {**(details or {}), "semester": semester}}
            write(path / "goal.json", goal)
            registry_path = path / "materials.json"
            if not registry_path.exists():
                write(registry_path, {"schema": 1, "revision": 0, "items": []})
            if not (path / "MAP.md").exists():
                atomic_text(path / "MAP.md", f"# {title}学习地图\n\n[学习对象入口](README.md) · [资料清单](MATERIALS.md) · [笔记](notes/)\n\n资料放入 `materials/` 后即可提问。当前没有已登记材料或正式笔记。\n\n## 疑问与薄弱点\n\n按需链接 records 中的记录；无证据不判断能力。\n")
            if not (path / "README.md").exists():
                atomic_text(path / "README.md", f"# {title}\n\n[原始资料](materials/) · [资料清单](MATERIALS.md) · [正式笔记](notes/) · [学习地图](MAP.md)\n\n课件、教材、作业、试卷等原始文件都直接放入 `materials/`；需要成组时再建子目录。\n\n`records/` 保存学习事件，`sessions/` 保存续接点，`pending/` 保存待核实内容；由 agent 管理。独立课程项目可放在 `projects/`。\n\n目标ID：`{goal_id}`。导入不等于学过。\n")
            self.write_materials_manifest(path, read(registry_path))
        self.refresh_navigation()
        return {"goal": goal_id, "materials": str(path / "materials")}

    def catalog(self):
        return [{**read(p), "path": p.parent.relative_to(self.root).as_posix()} for p in self.goal_files()]

    def refresh_navigation(self):
        """导航为可重建视图；目标身份仍以各 goal.json 为准。"""
        with lock(self.home / ".goals.lock"):
            goals = self.catalog()
            def table(items, base):
                rows = ["| 学习对象 | 资料 | 笔记 | 地图 |", "|---|---|---|---|"]
                for goal in items:
                    path = self.root / goal["path"]
                    def link(part):
                        return quote(Path(os.path.relpath(path / part, base)).as_posix(), safe="/")
                    title = str(goal['title']).replace('|', '\\|').replace('\n', ' ')
                    rows.append(f"| [{title}]({link('README.md')}) | [原件]({link('materials')}) | [笔记]({link('notes')}) | [地图]({link('MAP.md')}) |")
                return "\n".join(rows) if items else "尚未建立学习对象。按实际名称创建即可，不预设已经读过或学过。"
            atomic_text(self.home / "INDEX.md", "# 学习导航\n\n按实体目录分类；旧学期课程仍可直接学习和复习。\n\n[课程与学期](../courses/README.md) · [读论文](../papers/README.md) · [自主学习](../self-study/README.md) · [共享计划](PLAN.md) · [待归属资料](待归属/README.md)\n\n" + table(goals, self.home) + "\n\n目标ID供工具关联，不要求用户记忆；创建目标后自动刷新本导航。\n")
            for folder, title, explanation in (
                ("courses", "课程", "按学期 / 课程名组织。学期结束不隐藏课程，也不重置旧笔记状态。"),
                ("papers", "读论文", "每篇论文或明确的专题一个目录；materials 放原文，notes 放阅读笔记。"),
                ("self-study", "自主学习", "雅思、技能自学与个人学习项目按项目名称分目录；阶段计划不拆散长期资料。")):
                items = [g for g in goals if g["path"].startswith(folder + "/")]
                text = f"# {title}\n\n[返回总览](../README.md)\n\n{explanation}\n\n"
                if folder == "courses":
                    semesters = sorted({Path(g['path']).parts[1] for g in items})
                    for semester in semesters:
                        subset = [g for g in items if Path(g['path']).parts[1] == semester]
                        text += f"## [{semester}]({quote(semester, safe='')}/README.md)\n\n" + table(subset, self.root / folder) + "\n\n"
                        atomic_text(self.root / folder / semester / "README.md", f"# {semester} 课程\n\n[全部学期](../README.md)\n\n" + table(subset, self.root / folder / semester) + "\n")
                    if not semesters:
                        text += "尚未建立课程；创建时需提供学期。\n"
                else:
                    text += table(items, self.root / folder) + "\n"
                text += "\n各学习对象：`materials/` 原件，`notes/` 正文，`MAP.md` 地图，`pending/` 待核实内容；`records/` 和 `sessions/` 由 agent 管理。\n"
                atomic_text(self.root / folder / "README.md", text)

    def register(self, goal_id, source="用户放入；具体出处待确认", role="unclassified"):
        path = self.goal(goal_id)
        with lock(path / ".goal.lock"):
            registry = read(path / "materials.json")
            items = {item["id"]: item for item in registry["items"]}
            for item in items.values():
                item["available_paths"] = []
            unsupported = []
            for file in sorted((path / "materials").rglob("*")):
                rel = file.relative_to(path).as_posix()
                if any(part.startswith(".") for part in file.relative_to(path / "materials").parts):
                    continue
                if file.is_symlink() or not file.resolve().is_relative_to((path / "materials").resolve()):
                    raise ValueError("资料含外部链接，请使用普通文件或明确指定外部原件")
                if not file.is_file():
                    continue
                if file.suffix.lower() not in EXTENSIONS:
                    unsupported.append(rel)
                    continue
                digest = sha(file)
                item = items.setdefault(digest, {"id": digest, "sha256": digest, "size": file.stat().st_size, "paths": [], "available_paths": [], "source": source, "role": role, "registered_at": now(), "parse_status": "not_requested", "quality": "unverified"})
                if rel not in item["paths"]:
                    item["paths"].append(rel)
                item["available_paths"].append(rel)
            registry["items"] = list(items.values())
            registry["revision"] += 1
            write(path / "materials.json", registry)
            self.write_materials_manifest(path, registry)
            goal = read(path / "goal.json")
            if goal["status"] in {"awaiting_materials", "materials_ready"}:
                goal["status"] = "materials_ready" if any(i["available_paths"] for i in items.values()) else "awaiting_materials"
                write(path / "goal.json", goal)
        return {"unique_available": sum(bool(i["available_paths"]) for i in items.values()), "duplicates": [i["available_paths"] for i in items.values() if len(i["available_paths"]) > 1], "unsupported": unsupported, "revision": registry["revision"]}

    def write_materials_manifest(self, path, registry):
        """刷新资料清单；隐藏缓存不进入面向用户的目录索引。"""
        by_path = {relative: item for item in registry["items"] for relative in item.get("available_paths", [])}
        files = sorted(
            file for file in (path / "materials").rglob("*")
            if file.is_file() and not any(part.startswith(".") for part in file.relative_to(path / "materials").parts)
        )
        rows = ["| 文件 | 类型 | 用途 |", "|---|---|---|"]
        for file in files:
            relative = file.relative_to(path / "materials").as_posix()
            display = relative.replace("|", "\\|").replace("`", "\\`")
            url = quote(relative, safe="/")
            registered = (path / "materials" / Path(relative)).relative_to(path).as_posix()
            item = by_path.get(registered)
            kind = file.suffix.lstrip(".").upper() or "其他"
            role = item.get("role", "未登记") if item else "未登记或格式暂不支持"
            rows.append(f"| [`{display}`](materials/{url}) | {kind} | {role} |")
        title = read(path / "goal.json")["title"]
        intro = (f"# {title}：资料清单\n\n[返回学习对象](README.md) · [打开资料目录](materials/)\n\n"
                 "资料统一放在 `materials/`，子目录可选，不要求按作业、考试等类别整理。新增文件后由 agent 登记；清单只表示位置和用途，不表示已阅读或已核实。\n\n")
        if not files:
            rows = ["当前没有资料文件。"]
        atomic_text(path / "MATERIALS.md", intro + "\n".join(rows) + "\n")

    def open_session(self, goal_id, label):
        path = self.goal(goal_id)
        sid = uuid.uuid4().hex
        data = {"schema": 1, "id": sid, "goal": goal_id, "label": label, "revision": 0, "updated": now(), "material": None, "location": None, "summary": "", "open_questions": [], "next_step": "定位材料和当前问题"}
        write(path / "sessions" / f"{sid}.json", data)
        return data

    def annotate_material(self, goal_id, material, expected_revision, source, role, parse_status="not_requested", quality="unverified", cache=None):
        path = self.goal(goal_id)
        if parse_status not in {"not_requested", "parsed", "unavailable"} or quality not in {"unverified", "checked"}:
            raise ValueError("材料解析/校验状态不合法")
        if not source or not role:
            raise ValueError("需要来源和材料角色，未知时明确写待确认")
        if parse_status == "parsed" and (not cache or not inside(path, cache).is_file()):
            raise ValueError("解析成功必须引用本目标中实际存在的缓存")
        with lock(path / ".goal.lock"):
            registry = read(path / "materials.json")
            if registry["revision"] != expected_revision:
                raise ValueError("材料清单版本冲突，请重读")
            item = next((i for i in registry["items"] if i["id"] == material), None)
            if item is None:
                raise ValueError("材料ID不存在")
            item.update(source=source, role=role, parse_status=parse_status, quality=quality, cache=cache)
            registry["revision"] += 1
            write(path / "materials.json", registry)
        return {"revision": registry["revision"], "item": item}

    def checkpoint(self, goal_id, session, expected_revision, material, location, summary, open_questions, next_step):
        path = self.goal(goal_id)
        file = path / "sessions" / f"{identifier(session)}.json"
        if material:
            self.material_ref(path, material, location)
        if not summary or not next_step or not isinstance(open_questions, list):
            raise ValueError("检查点需要摘要、疑问列表和下一步")
        with lock(path / ".goal.lock"):
            data = read(file)
            if data["revision"] != expected_revision:
                raise ValueError("会话版本冲突；重读最新会话，不得覆盖")
            data.update(material=material, location=location, summary=summary, open_questions=open_questions, next_step=next_step, updated=now(), revision=data["revision"] + 1)
            write(file, data)
        return data

    def material_ref(self, path, material, location):
        if not location or not isinstance(location, str):
            raise ValueError("材料引用需要页码、章节、题号或时间段")
        items = read(path / "materials.json")["items"]
        item = next((i for i in items if i["id"] == material), None)
        if not item or not item["available_paths"]:
            raise ValueError("材料不存在或已替换，请重新定位原件")
        if not any((path / rel).is_file() and sha(path / rel) == item["sha256"] for rel in item["available_paths"]):
            raise ValueError("材料内容已变化，请重新登记")

    def events(self, goal_id):
        return sorted((read(p) for p in (self.goal(goal_id) / "records").glob("*.json")), key=lambda e: (e["at"], e["id"]))

    def record(self, goal_id, session, kind, topic, summary, evidence=None, material=None, location=None, task=None, event_id=None):
        path = self.goal(goal_id)
        if not (path / "sessions" / f"{identifier(session)}.json").is_file():
            raise ValueError("必须使用本目标的会话ID")
        if kind not in KINDS or not topic or not summary:
            raise ValueError("记录需要合法类型、主题和摘要")
        evidence = evidence or {}
        if material:
            self.material_ref(path, material, location)
        if kind in {"understanding", "mastery"}:
            if evidence.get("method") not in {"independent_explanation", "independent_application", "self_test", "external_result"} or not all(evidence.get(k) for k in ("observation", "basis", "result")):
                raise ValueError("理解或掌握必须有独立表现、评价依据和结果；自述懂了不算")
            if evidence["result"] not in {"pass", "partial", "fail"}:
                raise ValueError("证据结果必须为pass/partial/fail")
            if kind == "mastery" and (evidence["result"] != "pass" or not evidence.get("scope")):
                raise ValueError("掌握必须限定范围且评价结果为 pass")
        if kind == "studied" and not evidence.get("basis"):
            raise ValueError("学过需要用户明确陈述或可见学习行为依据")
        if kind == "resolved":
            refs = {e["id"] for e in self.events(goal_id) if e["kind"] in {"question", "mistake"}}
            if evidence.get("resolves") not in refs:
                raise ValueError("需要引用本目标待解决记录的ID")
        if kind == "mistake" and not all(evidence.get(k) for k in ("user_answer", "answer_source", "reason")):
            raise ValueError("错题需记录原选择、答案来源和错因；不清楚可写待核实")
        if kind == "task_progress":
            self.validate_progress(goal_id, task, evidence)
        eid = identifier(event_id or uuid.uuid4().hex)
        data = {"schema": 1, "id": eid, "goal": goal_id, "session": session, "kind": kind, "topic": topic, "summary": summary, "evidence": evidence, "material": material, "location": location, "task": task}
        with lock(path / ".goal.lock"):
            target = path / "records" / f"{eid}.json"
            if target.exists():
                old = read(target)
                if {k: v for k, v in old.items() if k != "at"} != data:
                    raise ValueError("事件ID已存在且内容不同")
                return old
            if kind == "task_progress":
                prior = [e for e in self.events(goal_id) if e["kind"] == "task_progress" and e["task"] == task]
                latest_id = prior[-1]["id"] if prior else None
                if evidence.get("previous_event") != latest_id:
                    raise ValueError("任务完成情况已更新；重读并引用previous_event后再记录，不能用旧进度覆盖")
            data["at"] = now()
            write(target, data)
        return data

    def validate_progress(self, goal_id, task, evidence):
        tasks = [t for p in (self.home / "plans").glob("*.json") for t in read(p).get("tasks", []) if t["goal"] == goal_id and t["id"] == task]
        ratio = evidence.get("completed_fraction")
        if not tasks or isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or not 0 <= ratio <= 1:
            raise ValueError("完成记录需要已规划任务和0至1的累计完成比例")
        if not evidence.get("basis") or not evidence.get("output"):
            raise ValueError("需要用户完成陈述/可见产出依据及产出位置")

    def resume(self, goal_id, session=None):
        path = self.goal(goal_id)
        sessions = sorted((read(p) for p in (path / "sessions").glob("*.json")), key=lambda x: x["updated"], reverse=True)
        events = self.events(goal_id)
        resolved = {e["evidence"].get("resolves") for e in events if e["kind"] == "resolved"}
        if session:
            identifier(session)
            selected = [s for s in sessions if s["id"] == session]
            if not selected:
                raise ValueError("找不到本目标会话")
        else:
            selected = sessions if len(sessions) == 1 else []
        sid = selected[0]["id"] if selected else None
        return {"goal": read(path / "goal.json"), "selection_required": len(sessions) > 1 and not session, "candidates": [{k: s[k] for k in ("id", "label", "updated", "summary", "location")} for s in sessions], "checkpoint": selected[0] if selected else None, "recent_records": [e for e in events if not sid or e["session"] == sid][-8:], "unresolved": [e for e in events if e["kind"] in {"question", "mistake"} and e["id"] not in resolved]}

    def progress(self, goal_id):
        path = self.goal(goal_id)
        events = self.events(goal_id)
        resolved = {e["evidence"].get("resolves") for e in events if e["kind"] == "resolved"}
        topics = {}
        for e in events:
            state = topics.setdefault(e["topic"], {"studied": [], "understanding_evidence": [], "mastery_evidence": [], "self_reports": [], "skipped_tests": [], "needs_review": []})
            key = {"studied": "studied", "understanding": "understanding_evidence", "mastery": "mastery_evidence", "self_report": "self_reports", "skip_test": "skipped_tests"}.get(e["kind"])
            if key:
                if e["kind"] == "understanding" and e["evidence"]["result"] != "pass":
                    state["needs_review"].append(e["id"])
                else:
                    state[key].append(e["id"])
            if e["kind"] == "mistake" and e["id"] not in resolved:
                state["needs_review"].append(e["id"])
        notes = [p for p in (path / "notes").rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(path / "notes").parts)]
        return {"imported_unique": sum(bool(i["available_paths"]) for i in read(path / "materials.json")["items"]), "notes_generated": len(notes), "topics": topics, "denominator": None, "warning": "没有确认学习单元总数，不计算全目标掌握百分比；证据需人核实"}

    def save_note(self, goal_id, relative, content, expected_sha256, sources, verified):
        path = self.goal(goal_id)
        target = inside(path, relative)
        if target != path / "MAP.md" and not target.is_relative_to(path / "notes"):
            raise ValueError("正式写入只接受 MAP.md 或 notes/*.md")
        if target.suffix != ".md" or not sources or verified is not True:
            raise ValueError("正式笔记需 Markdown、已核实标记和来源；否则放 pending")
        for source in sources:
            if source.get("material"):
                self.material_ref(path, source["material"], source["location"])
            else:
                external = Path(source.get("external_path", ""))
                if not external.is_absolute() or not external.is_file() or not source.get("location") or sha(external) != source.get("sha256"):
                    raise ValueError("外部原件需用户已指定的绝对路径、位置和当前SHA256")
        with lock(path / ".goal.lock"):
            current = sha(target) if target.exists() else None
            if current != expected_sha256:
                pending = path / "pending" / f"conflict-{uuid.uuid4().hex}.md"
                atomic_text(pending, content)
                return {"saved": False, "conflict": True, "candidate": str(pending), "current_sha256": current}
            if target.exists():
                backup = path / "notes/.history" / f"{uuid.uuid4().hex}-{target.name}"
                atomic_text(backup, target.read_text(encoding="utf-8"))
            provenance = path / "notes/.history" / f"{uuid.uuid4().hex}.json"
            # 先保存来源与目标内容指纹；中断后可按指纹判断正文是否完成落盘。
            write(provenance, {"target": relative, "intended_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(), "sources": sources, "verified_by_agent": True, "at": now()})
            atomic_text(target, content)
        return {"saved": True, "path": str(target), "sha256": sha(target), "provenance": str(provenance)}

    def task_fraction(self, goal_id, task_id):
        records = [e for e in self.events(goal_id) if e["kind"] == "task_progress" and e["task"] == task_id]
        return records[-1]["evidence"]["completed_fraction"] if records else 0

    def plan(self, start, days, tasks, save=False, deferred=None):
        first = date.fromisoformat(start)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 366:
            raise ValueError("计划天数应为1到366")
        availability = read(self.home / "availability.json")
        if availability.get("timezone") != "Asia/Shanghai":
            raise ValueError("时间预算必须明确使用 Asia/Shanghai")
        deferred = deferred or {}
        plans_before = sorted((self.home / "plans").glob("*.json"))
        records_before = self.records_snapshot()
        seen = set()
        work = []
        known = {t["id"]: t for p in sorted((self.home / "plans").glob("*.json")) for t in read(p).get("tasks", [])}
        for task in tasks:
            identifier(task["id"])
            if task["id"] in seen:
                raise ValueError("任务ID不可重复")
            seen.add(task["id"])
            path = self.goal(task["goal"])
            self.material_ref(path, task["material"], task["location"])
            minutes = task["minutes"]
            if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes <= 0 or not task.get("output") or not task.get("title"):
                raise ValueError("任务需正整数分钟、名称、具体产出")
            priority, weakness = task.get("priority", 2), task.get("weakness", 0)
            if priority not in (1, 2, 3) or weakness not in (0, 1, 2):
                raise ValueError("优先级应为1至3，弱项强度0至2（未知用0）")
            if task.get("deadline"):
                date.fromisoformat(task["deadline"])
            if task["id"] in known:
                old = known[task["id"]]
                if any(old[k] != task[k] for k in ("goal", "material", "location", "minutes", "output")):
                    raise ValueError("同一任务ID的材料、工作量和产出不可更换；拆分任务请用新ID")
            fraction = self.task_fraction(task["goal"], task["id"])
            work.append({**task, "remaining_minutes": math.ceil(minutes * (1 - fraction))})
        if plans_before:
            latest = read(plans_before[-1])
            for old in latest["tasks"]:
                if old["id"] not in seen and self.task_fraction(old["goal"], old["id"]) < 1 and not deferred.get(old["id"]):
                    raise ValueError("重排必须纳入所有目标的剩余任务；延期/移出须在deferred注明原因")
        # 截止日先于优先级、弱项；用户可调整候选任务。没有规则推测分数。
        work.sort(key=lambda t: (t.get("deadline") or "9999-12-31", -t.get("priority", 2), -t.get("weakness", 0), t["id"]))
        schedule = []
        for offset in range(days):
            day = first + timedelta(days=offset)
            key = day.isoformat()
            budget = availability.get("overrides", {}).get(key, availability.get("weekend_minutes" if day.weekday() >= 5 else "weekday_minutes"))
            if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
                raise ValueError(f"{key} 的时间预算尚未确认")
            remaining = budget
            selected = []
            for task in work:
                if task.get("deadline") and key > task["deadline"]:
                    continue
                amount = min(remaining, task["remaining_minutes"])
                if amount:
                    selected.append({"task": task["id"], "goal": task["goal"], "minutes": amount, "material": task["material"], "location": task["location"], "output": task["output"]})
                    task["remaining_minutes"] -= amount
                    remaining -= amount
            schedule.append({"date": key, "budget": budget, "allocated": budget - remaining, "tasks": selected})
        result = {"schema": 1, "id": uuid.uuid4().hex, "created": now(), "timezone": "Asia/Shanghai", "start": start, "days": days, "tasks": tasks, "deferred": deferred, "schedule": schedule, "unscheduled": [{"task": t["id"], "remaining_minutes": t["remaining_minutes"], "reason": "截止日或总预算不足，需缩减/延期/拆分，不能默认完成"} for t in work if t["remaining_minutes"]], "actual_completion": "从各目标 task_progress 记录读取；此计划不是完成证据"}
        if save:
            # 计划版本只新增；同一时间只有一个写入者。最新版本替代旧版本的未来安排。
            with lock(self.home / ".plan.lock"):
                records_after = self.records_snapshot()
                if sorted((self.home / "plans").glob("*.json")) != plans_before or records_after != records_before:
                    raise ValueError("规划期间计划或完成记录有更新，请按最新事实重新规划")
                write(self.home / "plans" / f"{result['created'].replace(':', '-')}-{result['id']}.json", result)
        return result

    def run(self, request):
        request = dict(request)
        action = request.pop("action")
        allowed = {"create", "adopt_course", "catalog", "refresh_navigation", "register", "annotate_material", "open_session", "checkpoint", "record", "resume", "progress", "save_note", "plan"}
        if action not in allowed:
            raise ValueError("未知操作")
        return getattr(self, action)(**request)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON 请求文件；见 learning/system/workflows.md")
    parser.add_argument("--root", type=Path, default=ROOT, help="仅在隔离演练时指定其他项目根目录")
    args = parser.parse_args()
    try:
        result = Learning(args.root).run(read(args.request))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
