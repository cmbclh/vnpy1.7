# encoding: utf-8

import urllib
import hashlib
import os
import jpype
from jpype import *
import math

import requests
from Queue import Queue, Empty
from threading import Thread
from time import sleep

LHANG_API_ROOT = "https://api.lhang.com/v1/"

FUNCTION_TICKER = 'FUNCTION_TICKER'
FUNCTION_ALL_TICKER = 'FUNCTION_ALL_TICKER'
FUNCTION_CREATEORDER = 'FUNCTION_CREATEORDER'


########################################################################
class GeyaBase(object):
    """"""
    DEBUG = True

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.apiKey = ''
        self.secretKey = ''

        self.interval = 1  # 每次请求的间隔等待
        self.active = False  # API工作状态
        self.reqID = 0  # 请求编号
        self.reqQueue = Queue()  # 请求队列
        self.reqThread = Thread(target=self.processQueue)  # 请求处理线程

    # ----------------------------------------------------------------------
    def init(self):
        """初始化"""
        self.active = True
        self.reqThread.start()

    # ----------------------------------------------------------------------
    def exit(self):
        """退出"""
        self.active = False

        if self.reqThread.isAlive():
            self.reqThread.join()

    # ----------------------------------------------------------------------
    # 需要进行改造，该接口需要进行高度抽象
    def processRequest(self, req):
        """处理请求"""
        # 读取方法和参数
        method = req['function']
        params = req['params']
        # url = LHANG_API_ROOT + api

        if method == FUNCTION_TICKER:  # 查询平盘最优额度
            r = self.queryTradePrice(params)
        elif method == FUNCTION_ALL_TICKER:  # 查询平盘全部额度，调用该服务结束后直接返回，因为该接口应答报文没有错误码
            r = self.queryAllTradePrice(params)
            data = {'code': '00000', 'resList': r}
            return  data
        elif method == FUNCTION_CREATEORDER:  # 平盘交易
            r = self.coverTrade(params)

        if r.code == '00000':
            if method == FUNCTION_TICKER:#查询最优平盘额度
                data = {'code': r.code, 'message': r.message, 'exnm': r.exnm, 'tradeSide': r.tradeSide, 'status': r.status,
                    'tradeLimitAmount': r.tradeLimitAmount, 'price': r.price}
            elif method == FUNCTION_CREATEORDER:  # 平盘交易，返回报文中可能有多条成交记录
                data = {'code': r.code, 'message': r.message, 'trsn': r.trsn, 'exnm': r.exnm, 'prcd': r.prcd,
                        'direction': params['tradeSide'], 'details': r.details}
        else:
            data = None

        return data

    # ----------------------------------------------------------------------
    def processQueue(self):
        """处理请求队列中的请求"""
        while self.active:
            try:
                req = self.reqQueue.get(block=True, timeout=1)  # 获取请求的阻塞为一秒
                #req = self.reqQueue.get(block=False)  # 获取请求的阻塞为一秒
                if req is None:
                    continue
                callback = req['callback']
                reqID = req['reqID']

                #判断java虚拟机是否启动，未启动则启动
                if jpype.isJVMStarted() == False:
                    # 启动java虚拟机
                    jarpath = os.path.join(os.path.abspath('.'), 'RmiInterface.jar')
                    print jarpath
                    print jpype.getDefaultJVMPath()
                    #jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
                    jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)

                data = self.processRequest(req)

                # 请求失败
                if data is None:
                    error = u'请求失败'
                    self.onError(error, req, reqID)
                # 请求成功
                elif data['code'] == '00000':
                    if self.DEBUG:
                        print callback.__name__
                    callback(data, req, reqID)
                # 请求失败
                else:
                    error = u'请求出错，错误代码：%s' % data['code']
                    self.onError(error, req, reqID)
                #finally:
                #    jpype.shutdownJVM()

                # 流控等待
                #sleep(self.interval)

            except Empty:
                pass
            except jpype.JavaException, ex:
                print ex.javaClass(),ex.message()
                print ex.stacktrace()
                # ----------------------------------------------------------------------

    def sendRequest(self, function, params, callback):
        """发送请求"""
        # 请求编号加1
        self.reqID += 1

        # 生成请求字典并放入队列中
        req = {}
        req['function'] = function
        req['params'] = params
        req['callback'] = callback
        req['reqID'] = self.reqID
        self.reqQueue.put(req)

        # 返回请求编号
        return self.reqID

    # ----------------------------------------------------------------------
    def onError(self, error, req, reqID):
        """错误推送"""
        print error, req, reqID

    ###############################################
    # 行情接口
    ###############################################

    # ----------------------------------------------------------------------
    def getTicker(self, symbol, direction, rmiIp, rmiPort):
        """#查询平盘最优额度"""
        function = FUNCTION_TICKER
        params = {'symbol': symbol,
                  'direction': direction,
                  'rmiIp': rmiIp,
                  'rmiPort': rmiPort}
        callback = self.onGetTicker
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def getDepth(self, symbol, rmiIp, rmiPort):
        """查询深度"""
        function = FUNCTION_ALL_TICKER
        params = {
            'symbol': symbol,
            'rmiIp': rmiIp,
            'rmiPort': rmiPort}
        callback = self.onGetDepth
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def onGetTicker(self, data, req, reqID):
        """查询行情回调"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onGetDepth(self, data, req, reqID):
        """查询深度回调"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onGetTrades(self, data, req, reqID):
        """查询历史成交"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onGetKline(self, data, req, reqID):
        """查询Ｋ线回报"""
        print data, reqID

    ###############################################
    # 交易接口
    ###############################################
    # ----------------------------------------------------------------------
    def createOrder(self, serial, prcd, exnm, reqDate, reqTime, volume, ppds, tradeSide, akpc, rrdc):
        """发送委托"""
        function = FUNCTION_CREATEORDER
        params = {
            'serial': serial,
            'prcd': prcd,
            'exnm': exnm,
            'reqDate': reqDate,
            'reqTime': reqTime,
            'volume': volume,
            'ppds': ppds,
            'tradeSide': tradeSide,
            'akpc': akpc,
            'rrdc': rrdc
        }
        callback = self.onCreateTrade
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def cancelOrder(self, symbol, orderId):
        """撤单"""
        function = FUNCTION_CANCELORDER
        params = {
            'symbol': symbol,
            'order_id': orderId
        }
        callback = self.onCancelOrder
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def getOrdersInfo(self, symbol, orderId):
        """查询委托"""
        function = FUNCTION_ORDERSINFO
        params = {
            'symbol': symbol,
            'order_id': orderId
        }
        callback = self.onGetOrdersInfo
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def getOrdersInfoHistory(self, symbol, status, currentPage, pageLength):
        """撤单"""
        function = FUNCTION_ORDERSINFOHISTORY
        params = {
            'symbol': symbol,
            'status': status,
            'current_page': currentPage,
            'page_length': pageLength
        }
        callback = self.onGetOrdersInfoHistory
        return self.sendRequest(function, params, callback)

    # ----------------------------------------------------------------------
    def onGetUserInfo(self, data, req, reqID):
        """查询账户信息"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onCreateOrder(self, data, req, reqID):
        """委托回报"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onCancelOrder(self, data, req, reqID):
        """撤单回报"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onGetOrdersInfo(self, data, req, reqID):
        """查询委托回报"""
        print data, reqID

    # ----------------------------------------------------------------------
    def onGetOrdersInfoHistory(self, data, req, reqID):
        """撤单回报"""
        print data, reqID

    # 调用自动平盘平台的查询平盘最优额度接口
    # def queryTradePrice(self, exnm, tradeSide, rmiIp, rmiPort):
    def queryTradePrice(self, params):
        Context = jpype.javax.naming.Context
        InitialContext = jpype.javax.naming.InitialContext
        namingContext = InitialContext()
        IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
        CheckHydraTradeInfoRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoRequest')
        # CheckHydraTradeInfoResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoResponse')
        TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
        # python调用java接口
        remoteObj = namingContext.lookup(
            "rmi://" + params['rmiIp'] + ":" + params['rmiPort'] + "/HydraTradeService")
        request = CheckHydraTradeInfoRequest()
        request.setExnm(params['symbol'])
        if params['direction'] == "BUY":
            request.setTradeSide(TradeSide.BUY)
        elif params['direction'] == "SELL":
            request.setTradeSide(TradeSide.SELL)

        resp = remoteObj.sendCheckForDeal(request)
        return resp

    # 调用自动平盘平台的查询全部平盘额度
    def queryAllTradePrice(self, params):
        Context = jpype.javax.naming.Context
        InitialContext = jpype.javax.naming.InitialContext
        namingContext = InitialContext()
        IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
        CheckHydraTradeAllInfoRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeAllInfoRequest')
        # CheckHydraTradeInfoResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CheckHydraTradeInfoResponse')
        # TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
        # python调用java接口
        remoteObj = namingContext.lookup(
            "rmi://" + params['rmiIp'] + ":" + params['rmiPort'] + "/HydraTradeService")
        request = CheckHydraTradeAllInfoRequest()
        request.setExnm(params['symbol'])
        resp = remoteObj.sendCheckForDealAll(request)
        return resp



    # 调用自动平盘平台的平盘交易接口
    def coverTrade(self, params):
        # jarpath = os.path.join(os.path.abspath('.'), 'RmiInterface.jar')
        # startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
        Context = jpype.javax.naming.Context
        InitialContext = jpype.javax.naming.InitialContext
        namingContext = InitialContext()
        IHydraTradeService = jpype.JClass('com.cmbc.hydra.rmi.service.IHydraTradeService')
        CallHydraTradeRequest = jpype.JClass('com.cmbc.hydra.rmi.bean.CallHydraTradeRequest')
        CallHydraTradeResponse = jpype.JClass('com.cmbc.hydra.rmi.bean.CallHydraTradeResponse')
        TradeSide = jpype.JClass('com.cmbc.hydra.rmi.bean.TradeSide')
        # python调用java接口
        remoteObj = namingContext.lookup(
            "rmi://" + self.gateway.rmiIp + ":" + self.gateway.rmiPort + "/HydraTradeService")
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

        BigDecimal = jpype.java.math.BigDecimal
        rmiRequst.setAmut(BigDecimal(params['volume']))
        rmiRequst.setAkpc(BigDecimal(params['akpc']))
        rmiRequst.setRrdc(BigDecimal(params['rrdc']))
        # resp = CheckHydraTradeInfoResponse()
        resp = remoteObj.callHydraTrade(rmiRequst)
        return resp