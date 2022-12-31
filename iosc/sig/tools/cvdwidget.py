"""CVD graphics widget."""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QResizeEvent
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
# 3. local
from iosc.sig.tools.cvdobject import CVDiagramObject


class CVDiagramView(QGraphicsView):
    """CVD graphics part."""

    cvdwin: 'CVDWindow'  # noqa: F821; uplink
    circle: CVDiagramObject  # downlink

    def __init__(self, parent: 'CVDWindow'):  # noqa: F821
        """Init CVDiagramView object."""
        # Howto (resize to content): scene.setSceneRect(scene.itemsBoundingRect()) <= QGraphicsScene::changed()
        super().__init__(parent)
        self.cvdwin = parent
        self.setScene(QGraphicsScene())
        # self.setMinimumSize(100, 100)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.circle = CVDiagramObject(self)
        self.scene().addItem(self.circle)

    def resizeEvent(self, event: QResizeEvent):
        """Inherited."""
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def reload_signals(self):
        """Reload vectors from selected signals.

        TODO: AnalogSignalSuit<=>SigVector map
        """
        self.circle.sv_clean()
        for r, ss in enumerate(self.cvdwin.ss_used):
            self.circle.sv_add(ss)

    def refresh_signals(self):
        """Refresh row values by ptr."""
        self.circle.sv_refresh()
