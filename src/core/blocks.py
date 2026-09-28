"""
Модель блоков отчёта.
Простые dataclass'ы — что именно показывать в отчёте.
"""

import pandas as pd

from dataclasses import dataclass, field


# ============================================================
# Базовый блок
# ============================================================

@dataclass
class Block:
    """Базовый блок."""
    id: str
    type: str
    title: str = ""
    
    def render(self) -> str:
        """Рендерит блок в HTML. Переопределяется в наследниках."""
        return f'<!-- block {self.id}: {self.type} -->'


# ============================================================
# Текстовые блоки
# ============================================================

@dataclass
class SectionTitleBlock(Block):
    """Заголовок раздела."""
    type: str = "section_title"
    
    def render(self) -> str:
        safe_title = _escape(self.title)
        return f'<h1 class="section-title">{safe_title}</h1>'


@dataclass
class ParagraphBlock(Block):
    """Параграф текста. Поддерживает HTML."""
    type: str = "paragraph"
    text: str = ""
    raw_html: bool = False
    
    def render(self) -> str:
        text = self.text if self.raw_html else _escape(self.text)
        paragraphs = [
            f"<p>{p.strip()}</p>" 
            for p in text.split("\n\n") 
            if p.strip()
        ]
        content = "".join(paragraphs) if paragraphs else "<p></p>"
        return (
            f'<div class="block">'
            f'<div class="block-card">'
            f'<div class="paragraph">{content}</div>'
            f'</div></div>'
        )


@dataclass
class ListBlock(Block):
    """Список пунктов."""
    type: str = "list"
    items: list[str] = field(default_factory=list)
    
    def render(self) -> str:
        items_html = "".join(
            f"<li>{_escape(item)}</li>" 
            for item in self.items
        )
        return (
            f'<div class="block">'
            f'<div class="block-card">'
            f'<ul class="block-list">{items_html}</ul>'
            f'</div></div>'
        )


@dataclass
class DividerBlock(Block):
    """Разделитель между разделами."""
    type: str = "divider"
    
    def render(self) -> str:
        return '<div class="section-divider"></div>'


# ============================================================
# KPI-блоки
# ============================================================

@dataclass
class KpiCard:
    """Одна KPI-карточка."""
    label: str
    value: str
    accent: bool = False


@dataclass
class KpiRowBlock(Block):
    """Ряд KPI-карточек."""
    type: str = "kpi_row"
    cards: list[KpiCard] = field(default_factory=list)
    
    def render(self) -> str:
        cards_html = []
        for card in self.cards:
            accent_class = " accent" if card.accent else ""
            cards_html.append(
                f'<div class="kpi-card">'
                f'<div class="kpi-value{accent_class}">{_escape(card.value)}</div>'
                f'<div class="kpi-label">{_escape(card.label)}</div>'
                f'</div>'
            )
        return (
            f'<div class="block">'
            f'<div class="kpi-row">{"".join(cards_html)}</div>'
            f'</div>'
        )


# ============================================================
# Блоки данных
# ============================================================

@dataclass
class DataTableBlock(Block):
    """
    Таблица с данными DataFrame.
    Показывает колонки в том порядке, в каком они переданы в visible_columns.
    """
    type: str = "data_table"
    dataframe: object = None
    max_rows: int = 20
    visible_columns: list[str] | None = None  # None = все, [] = ничего
    
    def render(self) -> str:
        if self.dataframe is None or len(self.dataframe) == 0:
            return self._render_empty()
        
        # Если явно передан пустой список → ничего не показываем
        if self.visible_columns is not None and len(self.visible_columns) == 0:
            return self._render_empty()
        
        df = self.dataframe
        
        # Определяем колонки для показа (СОХРАНЯЯ ПОРЯДОК из visible_columns)
        if self.visible_columns is None:
            cols = list(df.columns)
        else:
            cols = [c for c in self.visible_columns if c in df.columns]
        
        if not cols:
            return self._render_empty()
        
        # Ограничиваем колонками — в нужном порядке
        df = df[cols]
        
        # Заголовки
        headers_html = "".join(
            f"<th>{_escape(str(col))}</th>" 
            for col in df.columns
        )
        
        # Строки
        rows_html = []
        for _, row in df.iterrows():
            cells = []
            for col in df.columns:
                val = row[col]
                text = self._format_value(val)
                cells.append(f"<td>{_escape(text)}</td>")
            rows_html.append(f"<tr>{''.join(cells)}</tr>")
        
        return f'''
        <div class="block">
            <div class="block-card" style="padding: 0;">
                <div class="data-table-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr>{headers_html}</tr>
                        </thead>
                        <tbody>
                            {''.join(rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    
    def _render_empty(self) -> str:
        """Если нет данных для показа."""
        return '''
        <div class="block">
            <div class="block-card" style="text-align:center; padding: 60px 20px;">
                <p style="color:#888; font-size: 14px;">
                    Нет выбранных колонок
                </p>
                <p style="color:#888; font-size: 13px; margin-top: 12px;">
                    Поставь галочки в левой панели, чтобы показать колонки.
                </p>
            </div>
        </div>
        '''
    
    @staticmethod
    def _format_value(val) -> str:
        """Форматирует значение ячейки."""
        if pd.isna(val):
            return "—"
        if isinstance(val, float):
            if abs(val) < 1:
                return f"{val:.4f}".rstrip("0").rstrip(".")
            return f"{val:,.2f}"
        if isinstance(val, int):
            return f"{val:,}"
        return str(val)


# ============================================================
# Утилиты
# ============================================================

def _escape(text: str) -> str:
    """Простое экранирование HTML."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )