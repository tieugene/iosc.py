from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide2.QtCharts import QtCharts
from comtrade import Comtrade


class MainWidget(QWidget):
    chart: QtCharts.QChart
    chart_view: QtCharts.QChartView

    def __init__(self):
        QWidget.__init__(self)
        splitter = QSplitter(self)
        # self.panel_top = QWidget(splitter)
        # splitter.addWidget(self.panel_top)
        self.chart = QtCharts.QChart()
        # self.chart.setAnimationOptions(QtCharts.QChart.AllAnimations)
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        splitter.addWidget(self.chart_view)
        self.panel_bottom = QWidget(splitter)
        splitter.addWidget(self.panel_bottom)
        splitter.setOrientation(Qt.Vertical)
        # splitter.setStretchFactor(0, 0)
        # splitter.setStretchFactor(1, 0)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def plot_chart(self, rec: Comtrade):
        """

        :param rec:
        - rec.time:array[f] - time tiks
        - rec.analog[0]:array[f] - values
        - rec.analog_channel_ids[0]:str - value name (e.g. Ua)
        :return:
        """
        series = QtCharts.QLineSeries()
        # series.setName(rec.analog_channel_ids[0])
        # Filling QLineSeries
        for i, t in enumerate(rec.time):
            series.append(t, rec.analog[0][i])
        self.chart.addSeries(series)
        # Setting X-axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setTickCount(10)
        axis_x.setLabelFormat("%.2f")
        axis_x.setTitleText("Time")
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        # Setting Y-axis
        axis_y = QtCharts.QValueAxis()
        axis_y.setTickCount(10)
        axis_y.setLabelFormat("%.2f")
        axis_y.setTitleText(rec.analog_channel_ids[0])
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
