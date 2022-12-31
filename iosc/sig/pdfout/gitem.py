"""QGraphicsItem successors (application independent)."""
# 1. std
from typing import Union
# 2. 3rd
from PyQt5.QtCore import Qt, QRectF, QSizeF
from PyQt5.QtGui import QPen, QResizeEvent, QPainter
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsItem, QGraphicsItemGroup, QStyleOptionGraphicsItem,\
    QGraphicsSimpleTextItem, QGraphicsTextItem, QGraphicsRectItem
# 3. local
from .const import FONT_MAIN


# ---- Shortcuts ----
# simple successors with some predefines
class ThinPen(QPen):
    """Non-scalable QPen."""

    def __init__(self, color: Qt.GlobalColor, style: Qt.PenStyle = None):
        """Init ThinPen object."""
        super().__init__(color)
        self.setCosmetic(True)
        if style is not None:
            self.setStyle(style)


class PlainTextItem(QGraphicsSimpleTextItem):
    """Non-scalable plain text.

    Warn: on resize:
    - not changed: boundingRect(), pos(), scenePos()
    - not call: deviceTransform(), itemTransform(), transform(), boundingRegion()
    - call: paint()
    :todo: add [align](https://www.qtcentre.org/threads/51168-QGraphicsTextItem-center-based-coordinates)
    """

    def __init__(self, txt: str, color: Qt.GlobalColor = None):
        """Init PlainTextItem object."""
        super().__init__(txt)
        self.setFont(FONT_MAIN)
        if color:
            self.setBrush(color)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)


class RichTextItem(QGraphicsTextItem):
    """Non-scalable rich text."""

    def __init__(self, txt: str = None):
        """Init RichTextItem object."""
        super().__init__(txt)
        self.setFont(FONT_MAIN)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)


class GroupItem(QGraphicsItemGroup):
    """Custom item group."""

    def __init__(self):
        """Init GroupItem object."""
        super().__init__()

    def boundingRect(self) -> QRectF:  # set_size() fix
        """Bounding rect."""
        return self.childrenBoundingRect()


# ---- QGraphicsItem ----
class TCPlainTextItem(PlainTextItem):
    """Top-H-centered text."""

    __br: QRectF  # boundingRect()

    def __init__(self, txt: str):
        """Init TCPlainTextItem object."""
        super().__init__(txt)
        self.__br = super().boundingRect()

    def boundingRect(self) -> QRectF:
        """Bounding rect."""
        self.__br = super().boundingRect()
        self.__br.translate(-self.__br.width() / 2, 0.0)
        return self.__br

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        """H-center."""
        painter.translate(self.__br.left(), -self.__br.top())  # shift to top
        super().paint(painter, option, widget)


class ClipedPlainTextItem(PlainTextItem):
    """Clipped plain text.

    Used in: RecTextItem
    """

    def __init__(self, txt: str, color: Qt.GlobalColor = None):
        """Init ClipedPlainTextItem object."""
        super().__init__(txt, color)

    def boundingRect(self) -> QRectF:  # fix for upper br: return clipped size
        """Bounding rect."""
        if self.isClipped():
            return self.parentItem().boundingRect()
        return super().boundingRect()


class ClipedRichTextItem(RichTextItem):
    """Clipped rich text."""

    def __init__(self, txt: str = None):
        """Init ClipedRichTextItem object."""
        super().__init__(txt)

    def boundingRect(self) -> QRectF:  # fix for upper br: return clipped size
        """Bounding rect."""
        if self.isClipped():
            return self.parentItem().boundingRect()
        return super().boundingRect()


# ---- QGraphicsView
class GraphViewBase(QGraphicsView):
    """Basic QGraphicsView parent (auto-resizing)."""

    def __init__(self, parent: QWidget = None):
        """Init GraphViewBase object."""
        super().__init__(parent)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)

    def resizeEvent(self, event: QResizeEvent):  # !!! (resize __view to content)
        """Inherited."""
        # super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.IgnoreAspectRatio)  # expand to max
        # Note: KeepAspectRatioByExpanding is extremally CPU-greedy


# ---- Containers
class RectTextItem(GroupItem):
    """Text in border.

    Used in: HeaderItem
    Result: something strange.
    """

    text: Union[ClipedPlainTextItem, ClipedRichTextItem]
    rect: QGraphicsRectItem

    def __init__(self, txt: Union[ClipedPlainTextItem, ClipedRichTextItem]):
        """Init RectTextItem object."""
        super().__init__()
        # text
        self.text = txt
        self.addToGroup(self.text)
        # rect
        self.rect = QGraphicsRectItem(self.text.boundingRect())  # default size == text size
        self.rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)  # YES!!!
        self.rect.setPen(ThinPen(Qt.GlobalColor.transparent))
        self.addToGroup(self.rect)
        # clip label
        self.text.setParentItem(self.rect)

    def set_width(self, w: float):
        """Set self width."""
        self.prepareGeometryChange()  # not helps
        r = self.rect.rect()
        r.setWidth(w)
        self.rect.setRect(r)

    def set_height(self, h: float):
        """Set self height."""
        self.prepareGeometryChange()  # not helps
        r = self.rect.rect()
        r.setHeight(h)
        self.rect.setRect(r)

    def set_size(self, s: QSizeF):  # self.rect.rect() = self.rect.boundingRect() + 1
        """Set self size."""
        self.prepareGeometryChange()  # not helps
        r = self.rect.rect()
        r.setWidth(s.width())
        r.setHeight(s.height())
        self.rect.setRect(r)
