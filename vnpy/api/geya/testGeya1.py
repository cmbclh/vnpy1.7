# encoding: UTF-8
import os
import jpype
from jpype import *

# 调用自动平盘平台的平盘交易接口
params = {
    'symbol': 'XAUUSD'
}
jarpath = os.path.join(os.path.abspath('.'), 'RmiInterface.jar')
startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
Context = jpype.javax.naming.Context
InitialContext = jpype.javax.naming.InitialContext
namingContext = InitialContext()
IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
CheckHydraTradeAllInfoRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeAllInfoRequest')
# CheckHydraTradeInfoResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoResponse')
# TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
# python调用java接口
remoteObj = namingContext.lookup(
    "rmi://197.3.176.62:12113/HydraTradeService")
request = CheckHydraTradeAllInfoRequest()
request.setExnm(params['symbol'])
resp = remoteObj.sendCheckForDealAll(request)
for ele in resp:
    print ele.bid
    print ele.bidAmount
    print ele.ask
    print ele.askAmount
    print ele.counterPartyName

