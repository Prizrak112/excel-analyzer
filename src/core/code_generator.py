"""
Генератор Python-скрипта из истории операций.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import hmac
import hashlib


# ============================================================
# Обязательные строки (защита авторства)
# ============================================================

SIGNATURE_SECRET = "EA_2026_PROTECT_KEY_x9k2m7p4"
SIGNATURE_MARKER = "=== EXCEL ANALYZER SIGNATURE ==="
AUTHOR_NAME = "В. Рагимов"
AUTHOR_EMAIL = "v.ragimov@agroeco.ru"
APP_NAME = "Excel Analyzer"
APP_VERSION = "1.0"


def _make_signature() -> str:
    """Короткий HMAC от обязательных строк."""
    msg = f"{APP_NAME}|{AUTHOR_NAME}|{AUTHOR_EMAIL}|{SIGNATURE_MARKER}"
    sig = hmac.new(
        SIGNATURE_SECRET.encode(),
        msg.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return sig


SIGNATURE_HASH = _make_signature()


# ============================================================
# Обязательный блок (в докстринге)
# ============================================================

REQUIRED_HEADER_LINES = [
    "",
    f"{SIGNATURE_MARKER}",
    f"Сгенерировано приложением: {APP_NAME} v{APP_VERSION}",
    f"Автор: {AUTHOR_NAME}",
    f"По всем вопросам: {AUTHOR_EMAIL}",
    f"Контрольная метка: {SIGNATURE_HASH}",
    "Удаление или изменение этого блока — нарушение целостности скрипта.",
    f"{SIGNATURE_MARKER}",
    "",
]


# ============================================================
# Код проверки подписи (в теле скрипта)
# ============================================================

def _make_check_code() -> list:
    """Код для проверки докстринга при запуске."""
    marker = SIGNATURE_MARKER
    hash_val = SIGNATURE_HASH
    email = AUTHOR_EMAIL

    lines = []
    lines.append("")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("# ЗАЩИТА АВТОРСТВА — НЕ УДАЛЯТЬ")
    lines.append("# ============================================================")
    lines.append("def _check_signature():")
    lines.append('    """Проверяет целостность авторской подписи."""')
    lines.append("    import sys")
    lines.append("    expected_marker = " + repr(marker))
    lines.append("    expected_hash = " + repr(hash_val))
    lines.append("    expected_email = " + repr(email))
    lines.append("")
    lines.append("    doc = __doc__ or ''")
    lines.append("")
    lines.append("    if expected_marker not in doc or expected_hash not in doc:")
    lines.append('        print("=" * 60)')
    lines.append('        print("❌ Скрипт программы поврежден, просьба откатить файл")')
    lines.append('        print("=" * 60)')
    lines.append(f'        print("По вопросам: {email}")')
    lines.append('        print("=" * 60)')
    lines.append("        sys.exit(1)")
    lines.append("")
    lines.append("")
    lines.append("_check_signature()")
    lines.append("")
    lines.append("")
    return lines


# ============================================================
# Компрессор — свернуть историю до финального состояния
# ============================================================

class OperationCompressor:
    """Сжимает историю операций до финального состояния."""
    
    @classmethod
    def compress(cls, operations: list) -> list:
        final_dtype = {}
        initial_dtype = {}
        cast_changes_count = {}
        
        rename_map = {}
        
        for op in operations:
            t = op.type
            p = op.params
            
            if t == "cast_column":
                col = p["column"]
                if col not in initial_dtype:
                    initial_dtype[col] = p.get("prev_dtype", "unknown")
                final_dtype[col] = p["new_dtype"]
                cast_changes_count[col] = cast_changes_count.get(col, 0) + 1
            
            elif t == "rename_column":
                col = p["column"]
                new_name = p["new_name"]
                if col == new_name:
                    rename_map.pop(col, None)
                else:
                    rename_map[col] = new_name
        
        compacted = []
        
        # CAST — по одной на колонку (даже если вернулось к исходному)
        for col, new_dtype in final_dtype.items():
            initial = initial_dtype.get(col, "unknown")
            changes = cast_changes_count.get(col, 0)
            if changes == 0:
                continue
            compacted.append({
                "type": "cast_column",
                "params": {
                    "column": col,
                    "prev_dtype": initial,
                    "new_dtype": new_dtype,
                    "was_changes": changes > 1,
                    "changes_count": changes,
                }
            })
        
        # RENAME — одним блоком
        if rename_map:
            compacted.append({
                "type": "rename_columns_bulk",
                "params": {"mapping": dict(rename_map)}
            })
        
        # Остальные — как есть (без дублей)
        # toggle_column — чисто UI-настройка видимости, в скрипт не идёт
        skip = {"cast_column", "rename_column", "toggle_column"}
        seen_other = set()
        for op in operations:
            if op.type in skip:
                continue
            key = (op.type, str(op.params))
            if key in seen_other:
                continue
            seen_other.add(key)
            compacted.append({
                "type": op.type,
                "params": op.params,
            })
        
        return compacted


# ============================================================
# Генератор
# ============================================================

class CodeGenerator:
    def __init__(
        self,
        file_name: str = "data.xlsx",
        sheet_name: str = "Sheet1",
        output_name: str = "output.xlsx",
        reset_index: bool = False,
    ):
        self.file_name = file_name
        self.sheet_name = sheet_name
        self.output_name = output_name
        self.reset_index = reset_index
    
    def generate(self, operations: list) -> str:
        compacted = OperationCompressor.compress(operations)
        
        lines = []
        
        # ===== ДОКСТРИНГ =====
        lines.append('"""')
        lines.append("Автоматически сгенерированный скрипт обработки Excel")
        lines.append(f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        source_name = Path(self.file_name).name
        lines.append(f"Источник: {source_name}")
        lines.append(f"Лист: {self.sheet_name}")
        lines.append("")
        lines.append("Скрипт воспроизводит все действия, выполненные в Excel Analyzer.")
        lines.append("Можно запустить как есть или использовать в Jupyter.")
        
        # ← Обязательный блок
        for l in REQUIRED_HEADER_LINES:
            lines.append(l)
        
        lines.append('"""')
        lines.append("")
        
        # ===== ИМПОРТЫ =====
        lines.append("import pandas as pd")
        lines.append("import numpy as np")
        lines.append("from pathlib import Path")
        
        # ← Проверка подписи (сразу после импортов)
        for l in _make_check_code():
            lines.append(l)
        
        # ===== КОНФИГУРАЦИЯ =====
        lines.append("# ============================================================")
        lines.append("# КОНФИГУРАЦИЯ")
        lines.append("# ============================================================")
        lines.append(f'SOURCE_FILE = Path(r"{self.file_name}")')
        lines.append(f'SHEET_NAME = "{self.sheet_name}"')
        lines.append(f'OUTPUT_FILE = Path(r"{self.output_name}")')
        lines.append(f"RESET_INDEX = {self.reset_index}")
        lines.append("")
        lines.append("")
        
        # ===== MAIN =====
        lines.append("def main():")
        lines.append("    # ========================================================")
        lines.append("    # ШАГ 1: Загрузка данных")
        lines.append("    # ========================================================")
        lines.append('    print("Загрузка данных...")')
        lines.append("    df = pd.read_excel(SOURCE_FILE, sheet_name=SHEET_NAME)")
        lines.append('    print(f"  Загружено: {len(df)} строк, {len(df.columns)} колонок")')
        lines.append("")
        
        step_num = 2
        for op in compacted:
            block = self._render_operation(op, step_num)
            if block:
                lines.append(block)
                step_num += 1
        
        # ===== ИТОГ =====
        lines.append("    # ========================================================")
        lines.append("    # ИТОГ")
        lines.append("    # ========================================================")
        lines.append('    print(f"Готово: {len(df)} строк, {len(df.columns)} колонок")')
        lines.append("")
        lines.append("    if RESET_INDEX:")
        lines.append("        df = df.reset_index(drop=True)")
        lines.append("")
        lines.append('    print(f"Сохранение в {OUTPUT_FILE}...")')
        lines.append("    df.to_excel(OUTPUT_FILE, index=False)")
        lines.append('    print("✅ Готово!")')
        lines.append("")
        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append("    main()")
        
        return "\n".join(lines)
    
    def _render_operation(self, op: dict, step_num: int) -> str:
        t = op["type"]
        p = op["params"]
        lines = []
        
        lines.append("    # ========================================================")
        
        if t == "cast_column":
            col = p["column"]
            new_dtype = p["new_dtype"]
            old_dtype = p.get("prev_dtype", "unknown")
            lines.append(f'    # ШАГ {step_num}: Преобразовать "{col}" в {new_dtype}')
            if p.get("was_changes"):
                lines.append(f"    # (промежуточных изменений типа: {p.get('changes_count', 0)})")
            lines.append(f"    # Было: {old_dtype} → Стало: {new_dtype}")
            lines.append("    # ========================================================")
            lines.append(f'    print("Преобразование \\"{col}\\" в {new_dtype}...")')
            
            if new_dtype in ("int64", "int"):
                lines.append(f'    df["{col}"] = pd.to_numeric(df["{col}"], errors="coerce").fillna(0).astype("int64")')
            elif new_dtype in ("float64", "float"):
                lines.append(f'    df["{col}"] = pd.to_numeric(df["{col}"], errors="coerce")')
            elif new_dtype in ("datetime64[ns]", "datetime"):
                lines.append(f'    df["{col}"] = pd.to_datetime(df["{col}"], errors="coerce")')
            elif new_dtype in ("str", "string", "object"):
                lines.append(f'    df["{col}"] = df["{col}"].astype(str)')
            elif new_dtype in ("bool", "boolean"):
                lines.append(f'    df["{col}"] = df["{col}"].astype(bool)')
            else:
                lines.append(f"    # Неизвестный тип: {new_dtype}")
            lines.append("")
        
        elif t == "rename_columns_bulk":
            mapping = p["mapping"]
            lines.append(f"    # ШАГ {step_num}: Переименование колонок")
            lines.append("    # ========================================================")
            lines.append('    print("Переименование колонок...")')
            lines.append("    df = df.rename(columns={")
            for old, new in mapping.items():
                lines.append(f'        "{old}": "{new}",')
            lines.append("    })")
            lines.append("")
        
        elif t == "toggle_column":
            col = p["column"]
            visible = p["visible"]
            action = "видима" if visible else "скрыта"
            lines.append(f'    # ШАГ {step_num}: Колонка "{col}" — {action} (в UI)')
            lines.append("    # ========================================================")
            lines.append("    # (на данные не влияет — только для отображения)")
            lines.append("")
        
        elif t == "reorder_columns":
            new_order = p.get("new_order", [])
            lines.append(f"    # ШАГ {step_num}: Изменить порядок колонок")
            lines.append("    # ========================================================")
            lines.append('    print("Изменение порядка колонок...")')
            lines.append("    df = df[[")
            for col in new_order:
                lines.append(f'        "{col}",')
            lines.append("    ]]")
            lines.append("")
        
        elif t == "split_column":
            col = p["column"]
            mode = p["mode"]
            new_names = p.get("new_names", [])
            delete_original = p.get("delete_original", False)
            lines.append(f'    # ШАГ {step_num}: Разделить "{col}" на {len(new_names)} колонок')
            lines.append("    # ========================================================")
            lines.append(f'    print("Разделение колонки \\"{col}\\"...")')
            
            if mode == "separator":
                sep = p.get("separator", " ")
                if len(new_names) == 2:
                    lines.append(f'    df[["{new_names[0]}", "{new_names[1]}"]] = df["{col}"].str.split("{sep}", n=1, expand=True)')
                else:
                    lines.append(f'    split_parts = df["{col}"].str.split("{sep}", expand=True)')
                    for i, name in enumerate(new_names):
                        lines.append(f'    df["{name}"] = split_parts[{i}]')
            elif mode == "position":
                position = p.get("position", 0)
                lines.append(f'    df["{new_names[0]}"] = df["{col}"].str[:{position}]')
                lines.append(f'    df["{new_names[1]}"] = df["{col}"].str[{position}:]')
            
            if delete_original:
                lines.append(f'    df = df.drop(columns=["{col}"])')
            lines.append("")
        
        elif t == "delete_columns":
            cols = p.get("columns", [])
            lines.append(f"    # ШАГ {step_num}: Удалить колонки")
            lines.append("    # ========================================================")
            cols_str = ", ".join(f'"{c}"' for c in cols)
            lines.append(f"    df = df.drop(columns=[{cols_str}])")
            lines.append("")
        
        elif t == "filter":
            col = p.get("column")
            op_sign = p.get("op", "==")
            value = p.get("value")
            lines.append(f'    # ШАГ {step_num}: Фильтр {col} {op_sign} {value}')
            lines.append("    # ========================================================")
            val_str = f'"{value}"' if isinstance(value, str) else str(value)
            lines.append(f'    df = df[df["{col}"] {op_sign} {val_str}]')
            lines.append("")
        
        elif t == "remove_duplicates":
            cols = p.get("columns", [])
            lines.append(f"    # ШАГ {step_num}: Удалить дубликаты")
            lines.append("    # ========================================================")
            if cols:
                cols_str = ", ".join(f'"{c}"' for c in cols)
                lines.append(f"    df = df.drop_duplicates(subset=[{cols_str}])")
            else:
                lines.append("    df = df.drop_duplicates()")
            lines.append("")
        
        else:
            lines.append(f"    # ШАГ {step_num}: {t}")
            lines.append("    # ========================================================")
            lines.append("    # (не поддерживается в генераторе)")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================
# Утилита
# ============================================================

def generate_script(
    operations: list,
    file_name: str,
    sheet_name: str = "Sheet1",
    reset_index: bool = False,
) -> str:
    output_name = Path(file_name).stem + "_processed.xlsx"
    gen = CodeGenerator(
        file_name=file_name,
        sheet_name=sheet_name,
        output_name=output_name,
        reset_index=reset_index,
    )
    return gen.generate(operations)