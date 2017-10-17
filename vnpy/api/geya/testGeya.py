# encoding: UTF-8
import os
import jpype
from jpype import *

# jarpath = os.path.join(os.path.abspath('.'), 'RmiInterface.jar')
# startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
# Context = jpype.javax.naming.Context
# InitialContext = jpype.javax.naming.InitialContext
# namingContext = InitialContext()
# IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
# CheckHydraTradeInfoRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoRequest')
# #CheckHydraTradeInfoResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoResponse')
# TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
# # python调用java接口
# remoteObj = namingContext.lookup(
#     "rmi://197.3.176.62:12113/HydraTradeService")
# request = CheckHydraTradeInfoRequest()
# request.setExnm('XAUUSD')
# request.setTradeSide(TradeSide.BUY)
# # resp = CheckHydraTradeInfoResponse()
# resp = remoteObj.sendCheckForDeal(request)


# 调用自动平盘平台的平盘交易接口
params = {
    'serial': '1111',
    'prcd': 'P004',
    'exnm': 'XAUUSD',
    'reqDate': '20171011',
    'reqTime': '14:39:20',
    'volume': '1',
    'ppds': 'ICBC',
    'tradeSide': 'BUY',
    'akpc': '1000',
    'rrdc': '12'
}
jarpath = os.path.join(os.path.abspath('.'), 'RmiInterface.jar')
startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
Context = jpype.javax.naming.Context
InitialContext = jpype.javax.naming.InitialContext
namingContext = InitialContext()
IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
CallHydraTradeRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CallHydraTradeRequest')
CallHydraTradeResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CallHydraTradeResponse')
TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
# python调用java接口
remoteObj = namingContext.lookup(
    "rmi://197.3.176.62:12113/HydraTradeService")
rmiRequst = CallHydraTradeRequest()
rmiRequst.setTrsn(params['serial'])
rmiRequst.setPrcd(params['prcd'])
rmiRequst.setRqdt(params['reqDate'])
rmiRequst.setRqtm(params['reqTime'])
rmiRequst.setPpds(params['ppds'])
rmiRequst.setExnm(params['exnm'])  # 可能需要转换
if params['tradeSide'] == "BUY":
    rmiRequst.setTradeSide(TradeSide.BUY)
elif params['tradeSide'] == "SELL":
    rmiRequst.setTradeSide(TradeSide.SELL)

BigDecimal  = jpype.java.math.BigDecimal
rmiRequst.setAmut(BigDecimal(params['volume']))
rmiRequst.setAkpc(BigDecimal(params['akpc']))
rmiRequst.setRrdc(BigDecimal(params['rrdc']))
# resp = CheckHydraTradeInfoResponse()
resp = remoteObj.callHydraTrade(rmiRequst)

print resp