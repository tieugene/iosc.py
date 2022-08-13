from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide2.QtCharts import QtCharts
from comtrade import Comtrade


class OneChart(QtCharts.QChart):
    def __init__(self, v_name: str, t_list, v_list):
        QtCharts.QChart.__init__(self)
        series = QtCharts.QLineSeries()
        # series.setName(v_name)  # TODO: hide title
        # Filling QLineSeries
        for i, t in enumerate(t_list):
            series.append(t, v_list[i])
        self.addSeries(series)
        # Setting X-axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setTickCount(10)
        axis_x.setLabelFormat("%.2f")
        # axis_x.setTitleText("Time")  # hide h-legend
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
        splitter.addWidget(self.panel_analog)
        self.panel_status = QWidget(splitter)
        self.panel_status.setLayout(QVBoxLayout())
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

        def __plot(dst_panel: QWidget, src_id: list, src_data: list, src_time: list, num: int):
            for i in range(num):
                chart = OneChart(src_id[i], src_time, src_data[i])
                chart_view: QtCharts.QChartView = QtCharts.QChartView(chart)
                chart_view.setRenderHint(QPainter.Antialiasing)
                chart_view.resize(500, 200)
                self.panel_analog.layout().addWidget(chart_view)

        __plot(self.panel_analog, rec.analog_channel_ids, rec.analog, rec.time, min(rec.analog_count, 2))
        # __plot(self.panel_status, rec.status_channel_ids, rec.status, rec.time, min(rec.status_count, 3))
