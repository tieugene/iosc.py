from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide2.QtCharts import QtCharts
from comtrade import Comtrade


class OneChart(QtCharts.QChart):
    def __init__(self, v_name: str, t_list, v_list):
        QtCharts.QChart.__init__(self)
        series = QtCharts.QLineSeries()
        # series.setName(rec.analog_channel_ids[0])
        # Filling QLineSeries
        for i, t in enumerate(t_list):
            series.append(t, v_list[i])
        self.addSeries(series)
        # Setting X-axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setTickCount(10)
        axis_x.setLabelFormat("%.2f")
        axis_x.setTitleText("Time")
        self.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        # Setting Y-axis
        axis_y = QtCharts.QValueAxis()
        axis_y.setTickCount(10)
        axis_y.setLabelFormat("%.2f")
        axis_y.setTitleText(v_name)
        self.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)


class ChartsWidget(QWidget):
    panel_analog: QWidget
    panel_status: QWidget

    def __init__(self):
        QWidget.__init__(self)
        splitter = QSplitter(self)
        self.panel_analog = QWidget(splitter)
        self.panel_analog.setLayout(QVBoxLayout())
        self.panel_status = QWidget(splitter)
        splitter.addWidget(self.panel_analog)
        splitter.addWidget(self.panel_status)
        splitter.setOrientation(Qt.Vertical)
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def plot_chart(self, rec: Comtrade):
        """
        :param rec: Data
        :return:
        """
        chart = OneChart(rec.analog_channel_ids[0], rec.time, rec.analog[0])
        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        self.panel_analog.layout().addWidget(chart_view)

