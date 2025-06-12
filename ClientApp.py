from opcua import Client
from opcua.ua import UaStatusCodeError, Variant, VariantType
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QGridLayout, QLabel, QPushButton,
                             QLineEdit, QScrollArea, QVBoxLayout, QStatusBar, QMessageBox)
from PyQt5.QtCore import QTimer
import sys
import time
import logging

# 配置日志
log_file = "opcua_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OPCUA")

# PLC 连接信息
PLC_URL = "opc.tcp://192.168.1.10:4840"
USERNAME = "admin"
PASSWORD = "admin"

# 变量配置（123 个，按分组排序）
VARIABLES = {
    # CNC控制（14 个）
    "CNCStatus": {"node": "ns=2;s=Application.GVL_HMI.CNCStatus", "type": "Int16", "comment": "CNC状态", "writable": False},
    "CNCSourceNo": {"node": "ns=2;s=Application.GVL_HMI.CNCSourceNo", "type": "Int32", "comment": "CNC运行行号", "writable": False},
    "CNCwm": {"node": "ns=2;s=Application.GVL_HMI.CNCwm", "type": "UInt16", "comment": "CNC切割参数号", "writable": False},
    "CNCiLastSwitch": {"node": "ns=2;s=Application.GVL_HMI.CNCiLastSwitch", "type": "Int16", "comment": "CNC最终开关号", "writable": False},
    "CNC_MODE": {"node": "ns=2;s=Application.GVL_HMI.CNC_MODE", "type": "Boolean", "comment": "CNC模式", "writable": True},
    "CNC_Manual": {"node": "ns=2;s=Application.GVL_HMI.CNC_Manual", "type": "Boolean", "comment": "手动模式(非CNC)", "writable": True},
    "CNC_Ready": {"node": "ns=2;s=Application.GVL_HMI.CNC_Ready", "type": "Boolean", "comment": "CNC准备", "writable": True},
    "CNC_Start": {"node": "ns=2;s=Application.GVL_HMI.CNC_Start", "type": "Boolean", "comment": "CNC启动", "writable": True},
    "CNC_WKStop": {"node": "ns=2;s=Application.GVL_HMI.CNC_WKStop", "type": "Boolean", "comment": "CNC确认步", "writable": True},
    "CNC_Read1": {"node": "ns=2;s=Application.GVL_HMI.CNC_Read1", "type": "Boolean", "comment": "CNC读文件", "writable": True},
    "XY_HOME": {"node": "ns=2;s=Application.GVL_HMI.XY_HOME", "type": "Boolean", "comment": "XY回零", "writable": True},
    "CNC_Pause": {"node": "ns=2;s=Application.GVL_HMI.CNC_Pause", "type": "Boolean", "comment": "CNC暂停", "writable": True},
    "CNC_Stop": {"node": "ns=2;s=Application.GVL_HMI.CNC_Stop", "type": "Boolean", "comment": "CNC停止", "writable": True},
    "CNC_Resst": {"node": "ns=2;s=Application.GVL_HMI.CNC_Resst", "type": "Boolean", "comment": "CNC复位", "writable": True},
    # X轴（16 个）
    "X_POWER": {"node": "ns=2;s=Application.GVL_HMI.X_POWER", "type": "Boolean", "comment": "X轴使能", "writable": True},
    "X_REST": {"node": "ns=2;s=Application.GVL_HMI.X_REST", "type": "Boolean", "comment": "X轴复位", "writable": True},
    "X_Stop": {"node": "ns=2;s=Application.GVL_HMI.X_Stop", "type": "Boolean", "comment": "X轴停止", "writable": True},
    "X_JogNeg": {"node": "ns=2;s=Application.GVL_HMI.X_JogNeg", "type": "Boolean", "comment": "X轴正转", "writable": True},
    "X_Jogrev": {"node": "ns=2;s=Application.GVL_HMI.X_Jogrev", "type": "Boolean", "comment": "X轴反转", "writable": True},
    "X_MoveAbs": {"node": "ns=2;s=Application.GVL_HMI.X_MoveAbs", "type": "Boolean", "comment": "X轴定位", "writable": True},
    "X_HOME": {"node": "ns=2;s=Application.GVL_HMI.X_HOME", "type": "Boolean", "comment": "X轴回原点", "writable": True},
    "X_PosNow": {"node": "ns=2;s=Application.GVL_HMI.X_PosNow", "type": "REAL", "comment": "X轴当前位置", "writable": False},
    "X_MoveVel": {"node": "ns=2;s=Application.GVL_HMI.X_MoveVel", "type": "REAL", "comment": "X轴速度", "writable": True},
    "X_MoveABSPos": {"node": "ns=2;s=Application.GVL_HMI.X_MoveABSPos", "type": "REAL", "comment": "X轴定位位置", "writable": True},
    "X_MoveRelaDist": {"node": "ns=2;s=Application.GVL_HMI.X_MoveRelaDist", "type": "REAL", "comment": "X轴相对位移值", "writable": True},
    "X_Moveacc": {"node": "ns=2;s=Application.GVL_HMI.X_Moveacc", "type": "REAL", "comment": "X轴加速", "writable": True},
    "X_Movedec": {"node": "ns=2;s=Application.GVL_HMI.X_Movedec", "type": "REAL", "comment": "X轴减速", "writable": True},
    "X_Stopdec": {"node": "ns=2;s=Application.GVL_HMI.X_Stopdec", "type": "REAL", "comment": "X轴急停减速", "writable": True},
    "X_MoveRela_done": {"node": "ns=2;s=Application.GVL_HMI.X_MoveRela_done", "type": "Boolean", "comment": "X轴相对运动完成", "writable": False},
    "X_MoveAbs_done": {"node": "ns=2;s=Application.GVL_HMI.X_MoveAbs_done", "type": "Boolean", "comment": "X轴定位完成", "writable": False},
    # Y轴（16 个）
    "Y_POWER": {"node": "ns=2;s=Application.GVL_HMI.Y_POWER", "type": "Boolean", "comment": "Y轴使能", "writable": True},
    "Y_REST": {"node": "ns=2;s=Application.GVL_HMI.Y_REST", "type": "Boolean", "comment": "Y轴复位", "writable": True},
    "Y_Stop": {"node": "ns=2;s=Application.GVL_HMI.Y_Stop", "type": "Boolean", "comment": "Y轴停止", "writable": True},
    "Y_JogNeg": {"node": "ns=2;s=Application.GVL_HMI.Y_JogNeg", "type": "Boolean", "comment": "Y轴正转", "writable": True},
    "Y_Jogrev": {"node": "ns=2;s=Application.GVL_HMI.Y_Jogrev", "type": "Boolean", "comment": "Y轴反转", "writable": True},
    "Y_MoveAbs": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveAbs", "type": "Boolean", "comment": "Y轴定位", "writable": True},
    "Y_HOME": {"node": "ns=2;s=Application.GVL_HMI.Y_HOME", "type": "Boolean", "comment": "Y轴回原点", "writable": True},
    "Y_PosNow": {"node": "ns=2;s=Application.GVL_HMI.Y_PosNow", "type": "REAL", "comment": "Y轴当前位置", "writable": False},
    "Y_MoveVel": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveVel", "type": "REAL", "comment": "Y轴速度", "writable": True},
    "Y_MoveABSPos": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveABSPos", "type": "REAL", "comment": "Y轴定位位置", "writable": True},
    "Y_MoveRelaDist": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveRelaDist", "type": "REAL", "comment": "Y轴相对位移值", "writable": True},
    "Y_Moveacc": {"node": "ns=2;s=Application.GVL_HMI.Y_Moveacc", "type": "REAL", "comment": "Y轴加速", "writable": True},
    "Y_Movedec": {"node": "ns=2;s=Application.GVL_HMI.Y_Movedec", "type": "REAL", "comment": "Y轴减速", "writable": True},
    "Y_Stopdec": {"node": "ns=2;s=Application.GVL_HMI.Y_Stopdec", "type": "REAL", "comment": "Y轴急停减速", "writable": True},
    "Y_MoveRela_done": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveRela_done", "type": "Boolean", "comment": "Y轴相对运动完成", "writable": False},
    "Y_MoveAbs_done": {"node": "ns=2;s=Application.GVL_HMI.Y_MoveAbs_done", "type": "Boolean", "comment": "Y轴定位完成", "writable": False},
    # A轴（16 个）
    "A_POWER": {"node": "ns=2;s=Application.GVL_HMI.A_POWER", "type": "Boolean", "comment": "A轴使能", "writable": True},
    "A_REST": {"node": "ns=2;s=Application.GVL_HMI.A_REST", "type": "Boolean", "comment": "A轴复位", "writable": True},
    "A_Stop": {"node": "ns=2;s=Application.GVL_HMI.A_Stop", "type": "Boolean", "comment": "A轴停止", "writable": True},
    "A_JogNeg": {"node": "ns=2;s=Application.GVL_HMI.A_JogNeg", "type": "Boolean", "comment": "A轴正转", "writable": True},
    "A_Jogrev": {"node": "ns=2;s=Application.GVL_HMI.A_Jogrev", "type": "Boolean", "comment": "A轴反转", "writable": True},
    "A_MoveAbs": {"node": "ns=2;s=Application.GVL_HMI.A_MoveAbs", "type": "Boolean", "comment": "A轴定位", "writable": True},
    "A_HOME": {"node": "ns=2;s=Application.GVL_HMI.A_HOME", "type": "Boolean", "comment": "A轴回原点", "writable": True},
    "A_PosNow": {"node": "ns=2;s=Application.GVL_HMI.A_PosNow", "type": "REAL", "comment": "A轴当前位置", "writable": False},
    "A_MoveVel": {"node": "ns=2;s=Application.GVL_HMI.A_MoveVel", "type": "REAL", "comment": "A轴速度", "writable": True},
    "A_MoveABSPos": {"node": "ns=2;s=Application.GVL_HMI.A_MoveABSPos", "type": "REAL", "comment": "A轴定位位置", "writable": True},
    "A_MoveRelaDist": {"node": "ns=2;s=Application.GVL_HMI.A_MoveRelaDist", "type": "REAL", "comment": "A轴相对位移值", "writable": True},
    "A_Moveacc": {"node": "ns=2;s=Application.GVL_HMI.A_Moveacc", "type": "REAL", "comment": "A轴加速", "writable": True},
    "A_Movedec": {"node": "ns=2;s=Application.GVL_HMI.A_Movedec", "type": "REAL", "comment": "A轴减速", "writable": True},
    "A_Stopdec": {"node": "ns=2;s=Application.GVL_HMI.A_Stopdec", "type": "REAL", "comment": "A轴急停减速", "writable": True},
    "A_MoveRela_done": {"node": "ns=2;s=Application.GVL_HMI.A_MoveRela_done", "type": "Boolean", "comment": "A轴相对运动完成", "writable": False},
    "A_MoveAbs_done": {"node": "ns=2;s=Application.GVL_HMI.A_MoveAbs_done", "type": "Boolean", "comment": "A轴定位完成", "writable": False},
    # B轴（16 个）
    "B_POWER": {"node": "ns=2;s=Application.GVL_HMI.B_POWER", "type": "Boolean", "comment": "B轴使能", "writable": True},
    "B_REST": {"node": "ns=2;s=Application.GVL_HMI.B_REST", "type": "Boolean", "comment": "B轴复位", "writable": True},
    "B_Stop": {"node": "ns=2;s=Application.GVL_HMI.B_Stop", "type": "Boolean", "comment": "B轴停止", "writable": True},
    "B_Jogrev": {"node": "ns=2;s=Application.GVL_HMI.B_Jogrev", "type": "Boolean", "comment": "B轴反转", "writable": True},
    "B_JogNeg": {"node": "ns=2;s=Application.GVL_HMI.B_JogNeg", "type": "Boolean", "comment": "B轴正转", "writable": True},
    "B_MoveAbs": {"node": "ns=2;s=Application.GVL_HMI.B_MoveAbs", "type": "Boolean", "comment": "B轴定位", "writable": True},
    "B_HOME": {"node": "ns=2;s=Application.GVL_HMI.B_HOME", "type": "Boolean", "comment": "B轴回原点", "writable": True},
    "B_PosNow": {"node": "ns=2;s=Application.GVL_HMI.B_PosNow", "type": "REAL", "comment": "B轴当前位置", "writable": False},
    "B_MoveVel": {"node": "ns=2;s=Application.GVL_HMI.B_MoveVel", "type": "REAL", "comment": "B轴速度", "writable": True},
    "B_MoveABSPos": {"node": "ns=2;s=Application.GVL_HMI.B_MoveABSPos", "type": "REAL", "comment": "B轴定位位置", "writable": True},
    "B_MoveRelaDist": {"node": "ns=2;s=Application.GVL_HMI.B_MoveRelaDist", "type": "REAL", "comment": "B轴相对位移值", "writable": True},
    "B_Moveacc": {"node": "ns=2;s=Application.GVL_HMI.B_Moveacc", "type": "REAL", "comment": "B轴加速", "writable": True},
    "B_Movedec": {"node": "ns=2;s=Application.GVL_HMI.B_Movedec", "type": "REAL", "comment": "B轴减速", "writable": True},
    "B_Stopdec": {"node": "ns=2;s=Application.GVL_HMI.B_Stopdec", "type": "REAL", "comment": "B轴急停减速", "writable": True},
    "B_MoveRela_done": {"node": "ns=2;s=Application.GVL_HMI.B_MoveRela_done", "type": "Boolean", "comment": "B轴相对运动完成", "writable": False},
    "B_MoveAbs_done": {"node": "ns=2;s=Application.GVL_HMI.B_MoveAbs_done", "type": "Boolean", "comment": "B轴定位完成", "writable": False},
    # Z轴（16 个）
    "Z_POWER": {"node": "ns=2;s=Application.GVL_HMI.Z_POWER", "type": "Boolean", "comment": "Z轴使能", "writable": True},
    "Z_REST": {"node": "ns=2;s=Application.GVL_HMI.Z_REST", "type": "Boolean", "comment": "Z轴复位", "writable": True},
    "Z_Stop": {"node": "ns=2;s=Application.GVL_HMI.Z_Stop", "type": "Boolean", "comment": "Z轴停止", "writable": True},
    "Z_Jogrev": {"node": "ns=2;s=Application.GVL_HMI.Z_Jogrev", "type": "Boolean", "comment": "Z轴反转", "writable": True},
    "Z_JogNeg": {"node": "ns=2;s=Application.GVL_HMI.Z_JogNeg", "type": "Boolean", "comment": "Z轴正转", "writable": True},
    "Z_MoveAbs": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveAbs", "type": "Boolean", "comment": "Z轴定位", "writable": True},
    "Z_HOME": {"node": "ns=2;s=Application.GVL_HMI.Z_HOME", "type": "Boolean", "comment": "Z轴回原点", "writable": True},
    "Z_PosNow": {"node": "ns=2;s=Application.GVL_HMI.Z_PosNow", "type": "REAL", "comment": "Z轴当前位置", "writable": False},
    "Z_MoveVel": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveVel", "type": "REAL", "comment": "Z轴速度", "writable": True},
    "Z_MoveABSPos": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveABSPos", "type": "REAL", "comment": "Z轴定位位置", "writable": True},
    "Z_Moveacc": {"node": "ns=2;s=Application.GVL_HMI.Z_Moveacc", "type": "REAL", "comment": "Z轴加速", "writable": True},
    "Z_Movedec": {"node": "ns=2;s=Application.GVL_HMI.Z_Movedec", "type": "REAL", "comment": "Z轴减速", "writable": True},
    "Z_Stopdec": {"node": "ns=2;s=Application.GVL_HMI.Z_Stopdec", "type": "REAL", "comment": "Z轴急停减速", "writable": True},
    "Z_MoveRelaDist": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveRelaDist", "type": "REAL", "comment": "Z轴相对位移值", "writable": True},
    "Z_MoveRela_done": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveRela_done", "type": "Boolean", "comment": "Z轴相对运动完成", "writable": False},
    "Z_MoveAbs_done": {"node": "ns=2;s=Application.GVL_HMI.Z_MoveAbs_done", "type": "Boolean", "comment": "Z轴定位完成", "writable": False},
    # 密封测试（13 个）
    "CHAMBER_O2_OK_SEAL": {"node": "ns=2;s=Application.GVL_HMI.CHAMBER_O2_OK", "type": "Boolean", "comment": "氧含量OK", "writable": False},
    "AI_HP_O2_CONTENT_OUTPUT_SEAL": {"node": "ns=2;s=Application.GVL_HMI.AI_HP_O2_CONTENT_OUTPUT", "type": "Float", "comment": "高精度氧含量值", "writable": False},
    "AI_LP_O2_CONTENT_OUTPUT_SEAL": {"node": "ns=2;s=Application.GVL_HMI.AI_LP_O2_CONTENT_OUTPUT", "type": "Float", "comment": "低精度氧含量值", "writable": False},
    "AI_CHAMBER_PRESSURE_OUTPUT_SEAL": {"node": "ns=2;s=Application.GVL_HMI.AI_CHAMBER_PRESSURE_OUTPUT", "type": "REAL", "comment": "工作腔压力值", "writable": False},
    "AI_CHAMBER_O2_CONTENT_OUTPUT_SEAL": {"node": "ns=2;s=Application.GVL_HMI.AI_CHAMBER_O2_CONTENT_OUTPUT", "type": "REAL", "comment": "工作腔氧含量值(PPM)", "writable": False},
    "SOLENOID_VALVE_CONTROL_MODE": {"node": "ns=2;s=Application.GVL_HMI.SOLENOID_VALVE_CONTROL_MODE", "type": "Int16", "comment": "电磁阀控制模式", "writable": False},
    "MANUAL_TEST_MODE": {"node": "ns=2;s=Application.GVL_HMI.MANUAL_TEST_MODE", "type": "Boolean", "comment": "手动测试模式", "writable": True},
    "EXHAUST_VALVE_1_ENABLE_H_1": {"node": "ns=2;s=Application.GVL_HMI.EXHAUST_VALVE_1_ENABLE_H_1", "type": "Boolean", "comment": "排气阀1手动打开", "writable": True},
    "EXHAUST_VALVE_2_ENABLE_H_1": {"node": "ns=2;s=Application.GVL_HMI.EXHAUST_VALVE_2_ENABLE_H_1", "type": "Boolean", "comment": "排气阀2手动打开", "writable": True},
    "FAST_FLUX_VALVE_ENBLE_H_1": {"node": "ns=2;s=Application.GVL_HMI.FAST_FLUX_VALVE_ENBLE_H_1", "type": "Boolean", "comment": "快速气阀手动打开", "writable": True},
    "SLOW_FLUX_VALVE_ENBLE_H_1": {"node": "ns=2;s=Application.GVL_HMI.SLOW_FLUX_VALVE_ENBLE_H_1", "type": "Boolean", "comment": "慢速气阀手动打开", "writable": True},
    "AUTO_TEST_MODE": {"node": "ns=2;s=Application.GVL_HMI.AUTO_TEST_MODE", "type": "Boolean", "comment": "自动测试模式", "writable": True},
    "START_AIR_CLEAN": {"node": "ns=2;s=Application.GVL_HMI.START_AIR_CLEAN", "type": "Boolean", "comment": "自动洗气", "writable": True},
    # 激光和风机（10 个）
    "CHAMBER_O2_OK_LASER": {"node": "ns=2;s=Application.GVL_HMI.CHAMBER_O2_OK", "type": "Boolean", "comment": "氧含量OK", "writable": False},
    "AI_HP_O2_CONTENT_OUTPUT_LASER": {"node": "ns=2;s=Application.GVL_HMI.AI_HP_O2_CONTENT_OUTPUT", "type": "Float", "comment": "高精度氧含量值", "writable": False},
    "AI_LP_O2_CONTENT_OUTPUT_LASER": {"node": "ns=2;s=Application.GVL_HMI.AI_LP_O2_CONTENT_OUTPUT", "type": "Float", "comment": "低精度氧含量值", "writable": False},
    "AI_CHAMBER_O2_CONTENT_OUTPUT_LASER": {"node": "ns=2;s=Application.GVL_HMI.AI_CHAMBER_O2_CONTENT_OUTPUT", "type": "REAL", "comment": "工作腔氧含量值(PPM)", "writable": False},
    "AI_CHAMBER_PRESSURE_OUTPUT_LASER": {"node": "ns=2;s=Application.GVL_HMI.AI_CHAMBER_PRESSURE_OUTPUT", "type": "REAL", "comment": "工作腔压力值", "writable": False},
    "AI_FILTER_ELEMENT_PRESSURE_OUTPUT": {"node": "ns=2;s=Application.GVL_HMI.AI_FILTER_ELEMENT_PRESSURE_OUTPUT", "type": "REAL", "comment": "过滤系统风压反馈值(单位pa)", "writable": False},
    "AI_FILTER_ELEMENT_PRESSURE_SET_H": {"node": "ns=2;s=Application.GVL_HMI.AI_FILTER_ELEMENT_PRESSURE_SET_H", "type": "REAL", "comment": "过滤系统风压设定值", "writable": True},
    "DO_LASER_EXTERNAL_LIGHT_OUTPUT_H": {"node": "ns=2;s=Application.GVL_HMI.DO_LASER_EXTERNAL_LIGHT_OUTPUT_H", "type": "Boolean", "comment": "激光器光出使能", "writable": True},
    "RECIRCULATING_FAN_ON_H": {"node": "ns=2;s=Application.GVL_HMI.RECIRCULATING_FAN_ON_H", "type": "Boolean", "comment": "循环风机打开", "writable": True},
    "PRINT_SHIELD_TEST": {"node": "ns=2;s=Application.GVL_HMI.PRINT_SHIELD_TEST", "type": "Boolean", "comment": "屏蔽打印测试", "writable": True},
    # 工厂设置（6 个）
    "CNC_XygapVel": {"node": "ns=2;s=Application.GVL_HMI.CNC_XygapVel", "type": "REAL", "comment": "CNC速度", "writable": False},
    "CNC_XygapACC": {"node": "ns=2;s=Application.GVL_HMI.CNC_XygapACC", "type": "REAL", "comment": "CNC加速度", "writable": False},
    "CNC_XygapDEC": {"node": "ns=2;s=Application.GVL_HMI.CNC_XygapDEC", "type": "REAL", "comment": "CNC减速度", "writable": False},
    "CNCfDefaultVel": {"node": "ns=2;s=Application.GVL_HMI.CNCfDefaultVel", "type": "REAL", "comment": "CNC默认速度", "writable": False},
    "CNCfDefaultAccel": {"node": "ns=2;s=Application.GVL_HMI.CNCfDefaultAccel", "type": "REAL", "comment": "CNC默认加速度", "writable": False},
    "CNCfDefaultDecel": {"node": "ns=2;s=Application.GVL_HMI.CNCfDefaultDecel", "type": "REAL", "comment": "CNC默认减速度", "writable": False},
}

# 分组定义
GROUPED_VARIABLES = {
    "CNC控制": [
        "CNCStatus", "CNCSourceNo", "CNCwm", "CNCiLastSwitch",
        "CNC_MODE", "CNC_Manual", "CNC_Ready", "CNC_Start", "CNC_WKStop", "CNC_Read1",
        "XY_HOME", "CNC_Pause", "CNC_Stop", "CNC_Resst"
    ],
    "X轴": [
        "X_PosNow", "X_MoveRela_done", "X_MoveAbs_done",
        "X_POWER", "X_REST", "X_Stop", "X_JogNeg", "X_Jogrev", "X_MoveAbs", "X_HOME",
        "X_MoveVel", "X_MoveABSPos", "X_MoveRelaDist", "X_Moveacc", "X_Movedec", "X_Stopdec"
    ],
    "Y轴": [
        "Y_PosNow", "Y_MoveRela_done", "Y_MoveAbs_done",
        "Y_POWER", "Y_REST", "Y_Stop", "Y_JogNeg", "Y_Jogrev", "Y_MoveAbs", "Y_HOME",
        "Y_MoveVel", "Y_MoveABSPos", "Y_MoveRelaDist", "Y_Moveacc", "Y_Movedec", "Y_Stopdec"
    ],
    "A轴": [
        "A_PosNow", "A_MoveRela_done", "A_MoveAbs_done",
        "A_POWER", "A_REST", "A_Stop", "A_JogNeg", "A_Jogrev", "A_MoveAbs", "A_HOME",
        "A_MoveVel", "A_MoveABSPos", "A_MoveRelaDist", "A_Moveacc", "A_Movedec", "A_Stopdec"
    ],
    "B轴": [
        "B_PosNow", "B_MoveRela_done", "B_MoveAbs_done",
        "B_POWER", "B_REST", "B_Stop", "B_Jogrev", "B_JogNeg", "B_MoveAbs", "B_HOME",
        "B_MoveVel", "B_MoveABSPos", "B_MoveRelaDist", "B_Moveacc", "B_Movedec", "B_Stopdec"
    ],
    "Z轴": [
        "Z_PosNow", "Z_MoveRela_done", "Z_MoveAbs_done",
        "Z_POWER", "Z_REST", "Z_Stop", "Z_Jogrev", "Z_JogNeg", "Z_MoveAbs", "Z_HOME",
        "Z_MoveVel", "Z_MoveABSPos", "Z_Moveacc", "Z_Movedec", "Z_Stopdec", "Z_MoveRelaDist"
    ],
    "密封测试": [
        "CHAMBER_O2_OK_SEAL", "AI_HP_O2_CONTENT_OUTPUT_SEAL", "AI_LP_O2_CONTENT_OUTPUT_SEAL",
        "AI_CHAMBER_PRESSURE_OUTPUT_SEAL", "AI_CHAMBER_O2_CONTENT_OUTPUT_SEAL", "SOLENOID_VALVE_CONTROL_MODE",
        "MANUAL_TEST_MODE", "EXHAUST_VALVE_1_ENABLE_H_1", "EXHAUST_VALVE_2_ENABLE_H_1",
        "FAST_FLUX_VALVE_ENBLE_H_1", "SLOW_FLUX_VALVE_ENBLE_H_1", "AUTO_TEST_MODE", "START_AIR_CLEAN"
    ],
    "激光和风机": [
        "CHAMBER_O2_OK_LASER", "AI_HP_O2_CONTENT_OUTPUT_LASER", "AI_LP_O2_CONTENT_OUTPUT_LASER",
        "AI_CHAMBER_O2_CONTENT_OUTPUT_LASER", "AI_CHAMBER_PRESSURE_OUTPUT_LASER",
        "AI_FILTER_ELEMENT_PRESSURE_OUTPUT", "DO_LASER_EXTERNAL_LIGHT_OUTPUT_H", "RECIRCULATING_FAN_ON_H",
        "PRINT_SHIELD_TEST", "AI_FILTER_ELEMENT_PRESSURE_SET_H"
    ],
    "工厂设置": [
        "CNC_XygapVel", "CNC_XygapACC", "CNC_XygapDEC",
        "CNCfDefaultVel", "CNCfDefaultAccel", "CNCfDefaultDecel"
    ]
}

class OPCUAHandler:
    def __init__(self):
        self.client = None
        self.nodes = {}

    def connect(self):
        self.cleanup_sessions()
        self.client = Client(PLC_URL)
        self.client.set_user(USERNAME)
        self.client.set_password(PASSWORD)
        self.client.connect_timeout = 5
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client.connect()
                logger.info("Successfully connected to PLC")
                for var_name, info in VARIABLES.items():
                    self.nodes[var_name] = self.client.get_node(info["node"])
                    logger.info(f"Initialized node {var_name}: {info['node']}")
                return True
            except UaStatusCodeError as e:
                logger.error(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if "BadTooManySessions" in str(e):
                    logger.warning("Too many sessions detected, attempting cleanup...")
                    self.cleanup_sessions()
                time.sleep(1)
                if attempt == max_retries - 1:
                    logger.error("Max connection retries reached")
                    return False
            except Exception as e:
                logger.error(f"Unexpected connection error: {e}")
                return False

    def cleanup_sessions(self):
        try:
            if self.client:
                self.client.disconnect()
                logger.info("Disconnected existing client for cleanup")
            temp_client = Client(PLC_URL)
            temp_client.set_user(USERNAME)
            temp_client.set_password(PASSWORD)
            temp_client.connect_timeout = 5
            temp_client.connect()
            temp_client.disconnect()
            logger.info("Session cleanup completed successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")

    def read_values(self):
        values = {}
        start_time = time.time()
        try:
            for var_name, node in self.nodes.items():
                try:
                    values[var_name] = node.get_value()
                    logger.debug(f"Read {var_name}: {values[var_name]}")
                except UaStatusCodeError as e:
                    logger.error(f"Failed to read {var_name}: {str(e)} (Node: {node.nodeid.to_string()})")
                    values[var_name] = "N/A"
            elapsed_time = (time.time() - start_time) * 1000
            logger.debug(f"Read all values in {elapsed_time:.2f} ms")
            return values
        except Exception as e:
            logger.error(f"Read failed: {e}")
            return {}

    def write_value(self, var_name, value):
        try:
            node = self.nodes[var_name]
            var_type = VARIABLES[var_name]["type"]
            if var_type == "Boolean":
                node.set_value(Variant(bool(value), VariantType.Boolean))
            elif var_type in ["Float", "REAL"]:
                node.set_value(Variant(float(value), VariantType.Float))
            elif var_type == "Int16":
                node.set_value(Variant(int(value), VariantType.Int16))
            elif var_type == "Int32":
                node.set_value(Variant(int(value), VariantType.Int32))
            elif var_type == "UInt16":
                node.set_value(Variant(int(value), VariantType.UInt16))
            logger.info(f"Successfully wrote {value} to {var_name}")
            return True, f"{var_name} 已设置为 {value}"
        except UaStatusCodeError as e:
            if str(e).find("BadWriteNotSupported") != -1:
                try:
                    current_value = node.get_value()
                    if var_type in ["Float", "REAL"]:
                        success = abs(float(current_value) - float(value)) < 1e-6
                    else:
                        success = current_value == value
                    if success:
                        logger.info(f"Write to {var_name} succeeded despite BadWriteNotSupported (verified value: {current_value})")
                        return True, f"{var_name} 已设置为 {value}"
                    else:
                        logger.error(f"Write to {var_name} failed (verified value: {current_value}, expected: {value})")
                        return False, f"写入失败: 值未更新 (期望 {value}, 实际 {current_value})"
                except Exception as verify_error:
                    logger.error(f"Failed to verify write to {var_name}: {verify_error}")
                    return False, f"写入失败: 无法验证写入结果 ({str(verify_error)})"
            else:
                logger.error(f"Failed to write {var_name}: {e}")
                return False, f"写入失败: {e}"
        except ValueError as e:
            logger.error(f"Invalid value for {var_name}: {e}")
            return False, f"无效值: {e}"
        except Exception as e:
            logger.error(f"Unexpected write error for {var_name}: {e}")
            return False, f"写入错误: {e}"

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
                logger.info("Disconnected from PLC")
                self.cleanup_sessions()
            except Exception as e:
                logger.error(f"Disconnect failed: {e}")
            finally:
                self.client = None
                self.nodes = {}

class OPCUAGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC OPC UA 实时监控")
        self.setGeometry(100, 100, 1000, 800)
        self.opc_handler = OPCUAHandler()
        self.value_labels = {}
        self.entries = {}
        self.bool_buttons = {}  # 存储布尔型按钮
        self.is_running = True
        self.init_ui()
        self.start_opcua()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        for group_name, var_names in GROUPED_VARIABLES.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_content = QWidget()
            grid_layout = QGridLayout(scroll_content)

            # 按只读、布尔型、其他类型排序
            read_only_vars = [v for v in var_names if not VARIABLES[v]["writable"]]
            writable_bool_vars = [v for v in var_names if VARIABLES[v]["writable"] and VARIABLES[v]["type"] == "Boolean"]
            writable_other_vars = [v for v in var_names if VARIABLES[v]["writable"] and VARIABLES[v]["type"] != "Boolean"]
            sorted_var_names = read_only_vars + writable_bool_vars + writable_other_vars

            # 计算分组中最长中文注释长度
            max_comment_length = max(len(VARIABLES[var]["comment"]) for var in sorted_var_names) if sorted_var_names else 10
            button_width = max_comment_length * 13  # 按字体大小估算宽度
            
            row = 0
            for var_name in sorted_var_names:
                info = VARIABLES[var_name]
                # 注释在前，变量名在括号内
                label_text = f"{info['comment'] or var_name}"
                grid_layout.addWidget(QLabel(label_text), row, 0)
                self.value_labels[var_name] = QLabel("N/A")
                grid_layout.addWidget(self.value_labels[var_name], row, 1)
                if info["writable"]:
                    if info["type"] == "Boolean":
                        btn = QPushButton(info["comment"])
                        btn.setCheckable(True)
                        btn.setMinimumWidth(button_width)
                        btn.clicked.connect(lambda checked, v=var_name: self.toggle_boolean(v))
                        grid_layout.addWidget(btn, row, 2)
                        self.bool_buttons[var_name] = btn
                    elif info["type"] in ["Float", "REAL", "Int16", "Int32", "UInt16"]:
                        self.entries[var_name] = QLineEdit()
                        self.entries[var_name].setPlaceholderText("输入值")
                        grid_layout.addWidget(self.entries[var_name], row, 2)
                        btn = QPushButton("写入")
                        btn.clicked.connect(lambda checked, v=var_name: self.submit_value(v))
                        grid_layout.addWidget(btn, row, 3)
                else:
                    grid_layout.addWidget(QLabel(""), row, 2)  # 占位
                    grid_layout.addWidget(QLabel(""), row, 3)  # 占位
                row += 1

            scroll.setWidget(scroll_content)
            tab_layout.addWidget(scroll)
            tabs.addTab(tab, group_name)

        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(self.on_exit)
        main_layout.addWidget(exit_btn)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("未连接")
        self.setStatusBar(self.status_bar)

        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QLabel { font-size: 14px; padding: 5px; }
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 5px;
                border-radius: 3px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:checked { background-color: #dc3545; }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 13px;
            }
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected { background: #007bff; color: white; }
        """)

    def toggle_boolean(self, var_name):
        try:
            current_value = self.opc_handler.read_values().get(var_name, False)
            new_value = not current_value
            success, message = self.opc_handler.write_value(var_name, new_value)
            if success:
                self.value_labels[var_name].setText(str(new_value))
                self.bool_buttons[var_name].setChecked(new_value)
            else:
                QMessageBox.critical(self, "错误", message)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def submit_value(self, var_name):
        try:
            value = self.entries[var_name].text()
            if not value or not value.replace(".", "").replace("-", "").isdigit():
                QMessageBox.critical(self, "错误", "请输入有效的数字")
                return
            var_type = VARIABLES[var_name]["type"]
            if var_type in ["Float", "REAL"]:
                value = float(value)
            elif var_type in ["Int16", "Int32", "UInt16"]:
                value = int(value)
            success, message = self.opc_handler.write_value(var_name, value)
            if success:
                if var_type in ["Float", "REAL"]:
                    self.value_labels[var_name].setText(f"{value:.4f}")
                else:
                    self.value_labels[var_name].setText(str(value))
                self.entries[var_name].clear()
            else:
                QMessageBox.critical(self, "错误", message)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def update_values(self):
        if not self.is_running:
            return
        try:
            values = self.opc_handler.read_values()
            if values:
                for var_name, value in values.items():
                    if VARIABLES[var_name]["type"] in ["Float", "REAL"] and isinstance(value, (int, float)):
                        self.value_labels[var_name].setText(f"{value:.4f}")
                    else:
                        self.value_labels[var_name].setText(str(value))
                    # 同步布尔型按钮状态
                    if var_name in self.bool_buttons:
                        self.bool_buttons[var_name].setChecked(bool(value))
                self.status_bar.showMessage("已连接")
            else:
                self.status_bar.showMessage("连接中断")
            logger.info("Values updated")
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.status_bar.showMessage(f"错误: {str(e)}")

    def start_opcua(self):
        if self.opc_handler.connect():
            self.status_bar.showMessage("已连接")
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_values)
            self.timer.start(300)  # 300ms 刷新
        else:
            QMessageBox.critical(self, "错误", "无法连接到 PLC，请检查网络或配置")
            self.on_exit()

    def on_exit(self):
        self.is_running = False
        self.opc_handler.disconnect()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OPCUAGUI()
    window.show()
    sys.exit(app.exec_())