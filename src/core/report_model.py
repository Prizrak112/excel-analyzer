"""
Модель отчёта.
Описывает структуру: Report → Section → ReportBlock.
НЕ рендерит HTML — только хранит данные.
"""

import uuid
from dataclasses import dataclass, field


# ============================================================
# Блок отчёта
# ============================================================

@dataclass
class ReportBlock:
    """
    Один блок отчёта.
    Тип определяет, как рендерить.
    Config — параметры блока.
    """
    id: str
    type: str                    # "title" | "paragraph" | "kpi" | "chart" | ...
    config: dict = field(default_factory=dict)
    
    @classmethod
    def create(cls, block_type: str, config: dict | None = None) -> "ReportBlock":
        """Создать блок с авто-ID."""
        return cls(
            id=_generate_id(),
            type=block_type,
            config=config or {},
        )


# ============================================================
# Раздел отчёта
# ============================================================

@dataclass
class Section:
    """Раздел отчёта: заголовок + список блоков."""
    id: str
    title: str
    icon: str = "📊"
    expanded: bool = True
    blocks: list[ReportBlock] = field(default_factory=list)
    
    @classmethod
    def create(cls, title: str, icon: str = "📊") -> "Section":
        """Создать раздел с авто-ID."""
        return cls(
            id=_generate_id(),
            title=title,
            icon=icon,
        )
    
    def add_block(self, block: ReportBlock):
        """Добавить блок в конец раздела."""
        self.blocks.append(block)
    
    def remove_block(self, block_id: str):
        """Удалить блок по ID."""
        self.blocks = [b for b in self.blocks if b.id != block_id]
    
    def get_block(self, block_id: str) -> ReportBlock | None:
        """Найти блок по ID."""
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None
    
    def move_block(self, block_id: str, new_index: int):
        """Переместить блок на новую позицию."""
        block = self.get_block(block_id)
        if block is None:
            return
        
        self.blocks.remove(block)
        new_index = max(0, min(new_index, len(self.blocks)))
        self.blocks.insert(new_index, block)


# ============================================================
# Отчёт целиком
# ============================================================

@dataclass
class Report:
    """Отчёт: список разделов + общие настройки."""
    title: str = "Новый отчёт"
    sections: list[Section] = field(default_factory=list)
    theme: str = "gsm_green"
    
    # ---------- Разделы ----------
    
    def add_section(self, title: str, icon: str = "📊") -> Section:
        """Создать и добавить раздел."""
        section = Section.create(title, icon)
        self.sections.append(section)
        return section
    
    def remove_section(self, section_id: str):
        """Удалить раздел по ID."""
        self.sections = [s for s in self.sections if s.id != section_id]
    
    def get_section(self, section_id: str) -> Section | None:
        """Найти раздел по ID."""
        for s in self.sections:
            if s.id == section_id:
                return s
        return None
    
    def move_section(self, section_id: str, new_index: int):
        """Переместить раздел на новую позицию."""
        section = self.get_section(section_id)
        if section is None:
            return
        
        self.sections.remove(section)
        new_index = max(0, min(new_index, len(self.sections)))
        self.sections.insert(new_index, section)
    
    # ---------- Блоки ----------
    
    def find_block(self, block_id: str) -> tuple[Section, ReportBlock] | None:
        """Найти блок во всём отчёте. Возвращает (раздел, блок)."""
        for section in self.sections:
            block = section.get_block(block_id)
            if block is not None:
                return (section, block)
        return None
    
    # ---------- Утилиты ----------
    
    def is_empty(self) -> bool:
        """Отчёт пустой?"""
        return len(self.sections) == 0
    
    def get_stats(self) -> dict:
        """Статистика по отчёту."""
        total_blocks = sum(len(s.blocks) for s in self.sections)
        return {
            "sections": len(self.sections),
            "blocks": total_blocks,
        }


# ============================================================
# Утилиты
# ============================================================

def _generate_id() -> str:
    """Генерирует уникальный короткий ID."""
    return uuid.uuid4().hex[:8]