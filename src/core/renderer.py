"""
Рендерер блоков отчёта в HTML.
Принимает список блоков → возвращает HTML.
"""

from src.core.blocks import Block


class Renderer:
    """Рендерит список блоков в HTML."""
    
    def __init__(self):
        self.blocks: list[Block] = []
    
    def add(self, block: Block):
        """Добавить блок."""
        self.blocks.append(block)
    
    def clear(self):
        """Очистить все блоки."""
        self.blocks.clear()
    
    def render(self) -> str:
        """Рендерит все блоки в HTML."""
        html_parts = []
        for block in self.blocks:
            try:
                html_parts.append(block.render())
            except Exception as e:
                # Изоляция ошибок: если блок упал — показываем ERROR, остальное работает
                html_parts.append(self._render_error(block, e))
        return "\n".join(html_parts)
    
    def _render_error(self, block: Block, error: Exception) -> str:
        """Рендерит блок с ошибкой."""
        return f'''
        <div class="block">
            <div class="block-card error">
                <div class="block-error-title">⚠️ Ошибка в блоке</div>
                <div><b>Тип:</b> {block.type}</div>
                <div><b>ID:</b> {block.id}</div>
                <div><b>Ошибка:</b> {type(error).__name__}: {error}</div>
            </div>
        </div>
        '''


def render_blocks(blocks: list[Block]) -> str:
    """Утилита: рендерит список блоков."""
    r = Renderer()
    for b in blocks:
        r.add(b)
    return r.render()