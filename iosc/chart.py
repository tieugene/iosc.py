from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide2.QtCharts import QtCharts
from comtrade import Comtrade


class OneChart(QtCharts.QChart):
    def __init__(self, v_name: str, t_list: list, v_list: list, time0: float):
        def __decorate_x(s):
            # Setting X-axis
            axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
            axis.setTickType(QtCharts.QValueAxis.TicksDynamic)
            axis.setTickInterval(100)
            axis.setTickAnchor(1000 * time0)  # TODO: brush=black
            # print("Anchor:", 1000 * time0)
            axis.setLabelFormat("%d")
            # axis.setLabelsVisible(False)
            # axis_x.setTitleText("Time")  # axis label
            self.addAxis(axis, Qt.AlignBottom)
            s.attachAxis(axis)

        def __decorate_y(s):
            # Setting Y-axis
            axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
            axis.setTickAnchor(0)
            axis.setTickCount(5)
            # axis.setLabelFormat("%.1f")  # default
            axis.setLabelsVisible(False)
            # axis.setTitleText(v_name)  # axis label
            self.addAxis(axis, Qt.AlignLeft)
            s.attachAxis(axis)

        QtCharts.QChart.__init__(self)
        series = QtCharts.QLineSeries()
        # Filling QLineSeries
        for i, t in enumerate(t_list):
            series.append(1000*t, v_list[i])
        self.addSeries(series)
        # decoration
        __decorate_x(series)
        __decorate_y(series)
        # self.legend().setVisible(False)
        series.setName(v_name)
        self.legend().setAlignment(Qt.AlignLeft)


class ChartsWidget(QWidget):
    panel_analog: QWidget
    panel_status: QWidget

    def __init__(self):
        QWidget.__init__(self)
        splitter = QSplitter(self)
        # 1. analog part
        self.panel_analog = QWidget(splitter)
        self.panel_analog.setLayout(QVBoxLayout())
        splitter.addWidget(self.panel_analog)
        # 2. digital part
        # self.panel_status = QWidget(splitter)
        # self.panel_status.setLayout(QVBoxLayout())
        # splitter.addWidget(self.panel_status)
        # 3. lets go
        splitter.setOrientation(Qt.Vertical)
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def plot_chart(self, rec: Comtrade):
        """
        :param rec: Data
        :return:
        """

        def __plot(dst_panel: QWidget, src_id: list, src_data: list, src_time: list, num: int, trigger_time: float):
            for i in range(num):
                chart = OneChart(src_id[i], src_time, src_data[i], trigger_time)
                chart_view: QtCharts.QChartView = QtCharts.QChartView(chart)
                chart_view.setRenderHint(QPainter.Antialiasing)
                self.panel_analog.layout().addWidget(chart_view)

        __plot(self.panel_analog, rec.analog_channel_ids, rec.analog, rec.time, min(rec.analog_count, 2), rec.trigger_time)
        # __plot(self.panel_status, rec.status_channel_ids, rec.status, rec.time, min(rec.status_count, 3))
