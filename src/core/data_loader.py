"""
Загрузка данных из Excel/CSV файлов.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


# ============================================================
# Модель загруженных данных
# ============================================================

@dataclass
class LoadedData:
    """Загруженные данные + метаинформация."""
    
    source_path: str
    sheet_name: Optional[str]
    dataframe: pd.DataFrame
    columns: list[str]
    dtypes: dict[str, str]
    rows_count: int
    cols_count: int
    
    column_order: list[str] = field(default_factory=list)
    visible_columns: list[str] = field(default_factory=list)
    column_meta: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.column_order:
            self.column_order = list(self.columns)
        if not self.visible_columns:
            self.visible_columns = list(self.columns)
        if not self.column_meta:
            self.column_meta = {}
    
    # ---------- Мета-данные ----------
    
    def get_display_name(self, column: str) -> str:
        meta = self.column_meta.get(column, {})
        return meta.get("display_name", column)
    
    def set_display_name(self, column: str, display_name: str):
        if column not in self.columns:
            return
        if column not in self.column_meta:
            self.column_meta[column] = {}
        self.column_meta[column]["display_name"] = display_name
    
    def reset_column_meta(self, column: str):
        """Сбросить мета-данные колонки (при удалении/разделении)."""
        if column in self.column_meta:
            del self.column_meta[column]
    
    # ---------- Преобразование типа ----------
    
    def cast_column(self, column: str, new_dtype: str) -> tuple[bool, str]:
        """Преобразует тип данных колонки."""
        print(f"[cast_column] column='{column}', new_dtype='{new_dtype}'")
        
        if column not in self.columns:
            return False, f"Колонка '{column}' не найдена"
        
        try:
            series = self.dataframe[column]
            
            if new_dtype in ("int", "int64"):
                converted = pd.to_numeric(series, errors="coerce")
                if converted.isna().all():
                    return False, "Не удалось преобразовать в число"
                if converted.isna().any():
                    self.dataframe[column] = converted
                    self.dtypes[column] = "float64"
                    return True, "Преобразовано в float64 (есть пустые значения)"
                self.dataframe[column] = converted.astype("int64")
                self.dtypes[column] = "int64"
                return True, "Преобразовано в int64"
            
            elif new_dtype in ("float", "float64"):
                converted = pd.to_numeric(series, errors="coerce")
                if converted.isna().all():
                    return False, "Не удалось преобразовать в число"
                self.dataframe[column] = converted
                self.dtypes[column] = "float64"
                return True, "Преобразовано в float64"
            
            elif new_dtype in ("str", "string", "object"):
                self.dataframe[column] = series.astype(str)
                self.dtypes[column] = "str"
                return True, "Преобразовано в строку"
            
            elif new_dtype in ("datetime", "datetime64[ns]"):
                converted = pd.to_datetime(series, errors="coerce")
                if converted.isna().all():
                    return False, "Не удалось преобразовать в дату"
                self.dataframe[column] = converted
                self.dtypes[column] = "datetime64[ns]"
                return True, "Преобразовано в дату"
            
            elif new_dtype in ("bool", "boolean"):
                converted = series.astype(bool)
                self.dataframe[column] = converted
                self.dtypes[column] = "bool"
                return True, "Преобразовано в boolean"
            
            else:
                return False, f"Неизвестный тип: {new_dtype}"
        
        except Exception as e:
            return False, f"Ошибка: {type(e).__name__}: {e}"
    
    # ============================================================
    # РАЗДЕЛЕНИЕ КОЛОНКИ
    # ============================================================
    
    def split_column(
        self,
        column: str,
        mode: str,
        params: dict,
        new_names: list[str],
        delete_original: bool = False,
    ) -> tuple[bool, str]:
        """Универсальное разделение колонки."""
        print(f"[split_column] column='{column}', mode='{mode}'")
        
        if column not in self.columns:
            return False, f"Колонка '{column}' не найдена"
        
        if len(new_names) != 2:
            return False, "Нужно ровно 2 имени колонок"
        
        for name in new_names:
            if not name or not name.strip():
                return False, "Все имена колонок должны быть заполнены"
        
        if new_names[0] == new_names[1]:
            return False, "Имена колонок должны быть разными"
        
        # Проверяем конфликты, но исключаем исходную колонку, если удаляем
        existing_to_check = set(self.columns)
        if delete_original:
            existing_to_check.discard(column)
        
        for name in new_names:
            if name in existing_to_check:
                return False, f"Колонка '{name}' уже существует"
        
        try:
            series = self.dataframe[column]
            
            if mode == "marker":
                result = series.apply(lambda v: self._split_by_marker(v, **params))
            elif mode == "position":
                result = series.apply(lambda v: self._split_by_position(v, **params))
            elif mode == "separator":
                result = series.apply(lambda v: self._split_by_separator(v, **params))
            else:
                return False, f"Неизвестный режим: {mode}"
            
            parts_1 = result.apply(lambda t: t[0])
            parts_2 = result.apply(lambda t: t[1])
            
            orig_index = self.columns.index(column)
            name_1, name_2 = new_names[0], new_names[1]
            
            # ← ЕСЛИ УДАЛЯЕМ ИСХОДНУЮ — ДЕЛАЕМ ЭТО СНАЧАЛА
            if delete_original:
                self.dataframe = self.dataframe.drop(columns=[column])
                del self.dtypes[column]
                self.columns.remove(column)
                self.column_order.remove(column)
                self.visible_columns.remove(column)
                self.reset_column_meta(column)
                orig_index = min(orig_index, len(self.columns))
            
            # Вставляем новые колонки
            self.dataframe.insert(orig_index, name_1, parts_1)
            self.dataframe.insert(orig_index + 1, name_2, parts_2)
            
            self.dtypes[name_1] = str(parts_1.dtype)
            self.dtypes[name_2] = str(parts_2.dtype)
            
            self.columns.insert(orig_index, name_1)
            self.columns.insert(orig_index + 1, name_2)
            
            pos_in_order = min(orig_index, len(self.column_order))
            self.column_order.insert(pos_in_order, name_1)
            self.column_order.insert(pos_in_order + 1, name_2)
            
            pos_visible = min(orig_index, len(self.visible_columns))
            self.visible_columns.insert(pos_visible, name_1)
            self.visible_columns.insert(pos_visible + 1, name_2)
            
            self.cols_count = len(self.columns)
            
            return True, f"Колонка «{column}» разделена на «{name_1}» и «{name_2}»"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Ошибка: {type(e).__name__}: {e}"
    
    def _split_by_marker(
        self,
        value,
        marker: str,
        before: bool = True,
        keep_spaces: bool = False,
    ) -> tuple[str, str]:
        """Разделить строку по метке."""
        if pd.isna(value):
            return "", ""
        
        s = str(value)
        
        if not marker:
            return s, ""
        
        pos = s.find(marker)
        
        if pos < 0:
            result = s if keep_spaces else s.strip()
            return result, ""
        
        if before:
            part_1 = s[:pos]
            part_2 = s[pos:]
        else:
            part_1 = s[:pos + len(marker)]
            part_2 = s[pos + len(marker):]
        
        if not keep_spaces:
            part_1 = part_1.strip()
            part_2 = part_2.strip()
        
        return part_1, part_2
    
    def _split_by_position(
        self,
        value,
        position: int,
        keep_spaces: bool = False,
    ) -> tuple[str, str]:
        """Разделить строку после N-го символа."""
        if pd.isna(value):
            return "", ""
        
        s = str(value)
        
        if position <= 0 or position >= len(s):
            result = s if keep_spaces else s.strip()
            return result, ""
        
        part_1 = s[:position]
        part_2 = s[position:]
        
        if not keep_spaces:
            part_1 = part_1.strip()
            part_2 = part_2.strip()
        
        return part_1, part_2
    
    def _split_by_separator(
        self,
        value,
        separator: str,
        keep_spaces: bool = False,
    ) -> tuple[str, str]:
        """Разделить строку по разделителю."""
        if pd.isna(value):
            return "", ""
        
        s = str(value)
        
        if not separator:
            return s, ""
        
        pos = s.find(separator)
        
        if pos < 0:
            result = s if keep_spaces else s.strip()
            return result, ""
        
        part_1 = s[:pos]
        part_2 = s[pos + len(separator):]
        
        if not keep_spaces:
            part_1 = part_1.strip()
            part_2 = part_2.strip()
        
        return part_1, part_2
    
    # ---------- Разделение по правилам (визуальный режим) ----------
    
    def split_by_rules(
        self,
        column: str,
        rules: list,
        new_names: list[str],
        delete_original: bool = False,
    ) -> tuple[bool, str]:
        """Разделение колонки по правилам (визуальный режим)."""
        from src.core.rule_detector import RuleDetector
        
        print(f"[split_by_rules] column='{column}', rules={len(rules)}")
        
        if column not in self.columns:
            return False, f"Колонка '{column}' не найдена"
        
        if not rules:
            return False, "Нет правил для применения"
        
        expected_cols = len(rules) + 1
        if len(new_names) != expected_cols:
            return False, f"Нужно {expected_cols} имён колонок, получено {len(new_names)}"
        
        for name in new_names:
            if not name or not name.strip():
                return False, "Все имена колонок должны быть заполнены"
        
        if len(set(new_names)) != len(new_names):
            return False, "Имена колонок должны быть разными"
        
        # Проверяем конфликты, но исключаем исходную колонку, если удаляем
        existing_to_check = set(self.columns)
        if delete_original:
            existing_to_check.discard(column)
        
        for name in new_names:
            if name in existing_to_check:
                return False, f"Колонка '{name}' уже существует"
        
        try:
            series = self.dataframe[column]
            
            rows_parts = series.apply(
                lambda v: self._apply_rules_to_value(v, rules)
            )
            
            parts_lists = rows_parts.tolist()
            
            new_columns_data = []
            for i in range(expected_cols):
                col_data = [parts[i] if i < len(parts) else "" for parts in parts_lists]
                new_columns_data.append(col_data)
            
            orig_index = self.columns.index(column)
            
            # ← ЕСЛИ УДАЛЯЕМ ИСХОДНУЮ — ДЕЛАЕМ ЭТО СНАЧАЛА
            if delete_original:
                self.dataframe = self.dataframe.drop(columns=[column])
                del self.dtypes[column]
                self.columns.remove(column)
                self.column_order.remove(column)
                self.visible_columns.remove(column)
                self.reset_column_meta(column)
                orig_index = min(orig_index, len(self.columns))
            
            # Вставляем новые колонки
            for i, name in enumerate(new_names):
                self.dataframe.insert(orig_index + i, name, new_columns_data[i])
                self.dtypes[name] = "str"
                self.columns.insert(orig_index + i, name)
            
            pos_in_order = min(orig_index, len(self.column_order))
            for i, name in enumerate(new_names):
                self.column_order.insert(pos_in_order + i, name)
            
            pos_visible = min(orig_index, len(self.visible_columns))
            for i, name in enumerate(new_names):
                self.visible_columns.insert(pos_visible + i, name)
            
            self.cols_count = len(self.columns)
            
            names_str = ", ".join(f"«{n}»" for n in new_names)
            return True, f"Колонка «{column}» разделена на {len(new_names)} частей: {names_str}"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Ошибка: {type(e).__name__}: {e}"
    
    def _apply_rules_to_value(self, value, rules: list) -> list[str]:
        """Применяет правила к одной строке."""
        import pandas as pd
        from src.core.rule_detector import RuleDetector
        
        expected_cols = len(rules) + 1
        
        if pd.isna(value):
            return [""] * expected_cols
        
        s = str(value)
        
        positions = []
        for rule in rules:
            pos = RuleDetector._find_split_position(rule, s)
            if pos is not None and 0 < pos < len(s):
                positions.append(pos)
        
        positions = sorted(set(positions))
        
        if not positions:
            return [s.strip()] + [""] * (expected_cols - 1)
        
        parts = []
        prev = 0
        for pos in positions:
            parts.append(s[prev:pos].strip())
            prev = pos
        parts.append(s[prev:].strip())
        
        while len(parts) < expected_cols:
            parts.append("")
        
        return parts[:expected_cols]
    
    # ---------- Preview разделения ----------
    
    def preview_split(
        self,
        column: str,
        mode: str,
        params: dict,
        n: int = 5,
    ) -> list[tuple[str, str]]:
        """Возвращает первые N строк после разделения."""
        if column not in self.columns:
            return []
        
        series = self.dataframe[column].head(n)
        
        try:
            if mode == "marker":
                result = series.apply(lambda v: self._split_by_marker(v, **params))
            elif mode == "position":
                result = series.apply(lambda v: self._split_by_position(v, **params))
            elif mode == "separator":
                result = series.apply(lambda v: self._split_by_separator(v, **params))
            else:
                return []
            
            return list(result)
        except Exception as e:
            print(f"[preview_split] Ошибка: {e}")
            return []
    
    # ---------- Preview данных ----------
    
    def get_preview(self, n: int = 20, columns: list[str] | None = None) -> pd.DataFrame:
        cols = columns if columns is not None else self.visible_columns
        cols = [c for c in cols if c in self.columns]
        return self.dataframe[cols].head(n)
    
    def get_renamed_preview(self, n: int = 20) -> pd.DataFrame:
        """Оптимизированная версия — сначала head, потом cols."""
        df_head = self.dataframe.head(n)
        cols = [c for c in self.visible_columns if c in self.columns]
        df = df_head[cols].copy()
        rename_map = {c: self.get_display_name(c) for c in df.columns}
        return df.rename(columns=rename_map)
    
    # ---------- Видимость ----------
    
    def show_all_columns(self):
        self.visible_columns = [c for c in self.column_order if c in self.columns]
    
    def hide_all_columns(self):
        self.visible_columns = []
    
    def toggle_column(self, column: str, visible: bool):
        if column not in self.columns:
            return
        
        if visible:
            if column not in self.visible_columns:
                col_pos = self.column_order.index(column)
                insert_pos = len(self.visible_columns)
                for i, vc in enumerate(self.visible_columns):
                    if vc in self.column_order and self.column_order.index(vc) > col_pos:
                        insert_pos = i
                        break
                self.visible_columns.insert(insert_pos, column)
        else:
            if column in self.visible_columns:
                self.visible_columns.remove(column)
    
    def is_column_visible(self, column: str) -> bool:
        return column in self.visible_columns
    
    # ---------- Порядок ----------
    
    def reorder_visible_columns(self, new_visible_order: list[str]):
        self.visible_columns = [c for c in new_visible_order if c in self.columns]
        hidden = [c for c in self.column_order if c not in self.visible_columns]
        self.column_order = list(self.visible_columns) + hidden
    
    # ---------- Информация ----------
    
    def get_columns_info(self) -> list[dict]:
        """Оптимизированная версия — кэширует информацию."""
        cache_key = (
            len(self.columns),
            self.cols_count,
            len(self.visible_columns),
        )
        
        if hasattr(self, "_columns_info_cache") and self._columns_info_cache_key == cache_key:
            return self._columns_info_cache
        
        info = []
        for col in self.columns:
            dtype = str(self.dtypes.get(col, "unknown"))
            
            info.append({
                "name": col,
                "display_name": self.get_display_name(col),
                "dtype": dtype,
                "n_unique": int(self.dataframe[col].nunique()),
                "n_nulls": int(self.dataframe[col].isnull().sum()),
                "visible": self.is_column_visible(col),
            })
        
        self._columns_info_cache = info
        self._columns_info_cache_key = cache_key
        return info
    
    def get_column_info(self, column: str) -> dict | None:
        for info in self.get_columns_info():
            if info["name"] == column:
                return info
        return None
    
    def invalidate_cache(self):
        """Сбросить кэш после изменений."""
        if hasattr(self, "_columns_info_cache"):
            del self._columns_info_cache


# ============================================================
# Загрузчик
# ============================================================

class DataLoader:
    """Загружает данные из файлов."""
    
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}
    
    @classmethod
    def get_excel_sheets(cls, filepath: str) -> list[str]:
        try:
            xls = pd.ExcelFile(filepath)
            return xls.sheet_names
        except Exception as e:
            raise RuntimeError(f"Не удалось прочитать листы: {e}")
    
    @classmethod
    def load_excel(cls, filepath: str, sheet_name: str | int = 0) -> LoadedData:
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        
        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Неподдерживаемый формат: {path.suffix}")
        
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        df = df.dropna(axis=1, how="all")
        df = df.dropna(axis=0, how="all")
        
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        return LoadedData(
            source_path=str(path),
            sheet_name=str(sheet_name) if sheet_name is not None else None,
            dataframe=df,
            columns=list(df.columns),
            dtypes=dtypes,
            rows_count=len(df),
            cols_count=len(df.columns),
        )
    
    @classmethod
    def load(cls, filepath: str, sheet_name: str | int = 0) -> LoadedData:
        return cls.load_excel(filepath, sheet_name)