# encoding: UTF-8
import datetime
import time
import json
import os
import jpype
from jpype import *

from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath
from language import text
from vnpy.api.geya.geyaApi import GeyaBase

SYMBOL_XAUUSD = 'XAUUSD'
SYMBOL_XAGUSD = 'XAGUSD'

SYMBOL_MAP = {}
SYMBOL_MAP['XAUUSD'] = SYMBOL_XAUUSD
SYMBOL_MAP['XAGUSD'] = SYMBOL_XAGUSD

#平盘对手数据字典
COUNTERPARTYNAME = {}
COUNTERPARTYNAME['GOLDSACHS'] = 'GOLDSACHS'
COUNTERPARTYNAME['UBS_ZUR'] = 'UBS_ZUR'

TRADE_DIRECTION = {}
TRADE_DIRECTION['BUY'] = 'BUY'
TRADE_DIRECTION['SELL'] = 'SELL'

GEYA_PRODUCT_CLASS = 'P004'

# encoding: UTF-8

# 默认空值
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

# 方向常量
DIRECTION_NONE = u'none'
DIRECTION_LONG = u'多'
DIRECTION_SHORT = u'空'
DIRECTION_UNKNOWN = u'unknown'
DIRECTION_NET = u'net'
DIRECTION_SELL = u'sell'      # IB接口
DIRECTION_COVEREDSHORT = u'covered short'    # 证券期权

# 开平常量
OFFSET_NONE = u'none'
OFFSET_OPEN = u'open'
OFFSET_CLOSE = u'close'
OFFSET_CLOSETODAY = u'close today'
OFFSET_CLOSEYESTERDAY = u'close yesterday'
OFFSET_UNKNOWN = u'unknown'

# 状态常量
STATUS_NOTTRADED = u'pending'
STATUS_PARTTRADED = u'partial filled'
STATUS_ALLTRADED = u'filled'
STATUS_CANCELLED = u'cancelled'
STATUS_REJECTED = u'rejected'
STATUS_UNKNOWN = u'unknown'

# 合约类型常量
PRODUCT_EQUITY = u'equity'
PRODUCT_FUTURES = u'futures'
PRODUCT_OPTION = u'option'
PRODUCT_INDEX = u'index'
PRODUCT_COMBINATION = u'combination'
PRODUCT_FOREX = u'forex'
PRODUCT_UNKNOWN = u'unknown'
PRODUCT_SPOT = u'spot'
PRODUCT_DEFER = u'defer'
PRODUCT_NONE = 'none'

# 价格类型常量
PRICETYPE_LIMITPRICE = u'limit order'
PRICETYPE_MARKETPRICE = u'market order'
PRICETYPE_FAK = u'FAK'
PRICETYPE_FOK = u'FOK'

# 期权类型
OPTION_CALL = u'call'
OPTION_PUT = u'put'

# 交易所类型
EXCHANGE_SSE = 'SSE'       # 上交所
EXCHANGE_SZSE = 'SZSE'     # 深交所
EXCHANGE_CFFEX = 'CFFEX'   # 中金所
EXCHANGE_SHFE = 'SHFE'     # 上期所
EXCHANGE_CZCE = 'CZCE'     # 郑商所
EXCHANGE_DCE = 'DCE'       # 大商所
EXCHANGE_SGE = 'SGE'       # 上金所
EXCHANGE_INE = 'INE'       # 国际能源交易中心
EXCHANGE_UNKNOWN = 'UNKNOWN'# 未知交易所
EXCHANGE_NONE = ''          # 空交易所
EXCHANGE_HKEX = 'HKEX'      # 港交所
EXCHANGE_HKFE = 'HKFE'      # 香港期货交易所

EXCHANGE_SMART = 'SMART'       # IB智能路由（股票、期权）
EXCHANGE_NYMEX = 'NYMEX'       # IB 期货
EXCHANGE_GLOBEX = 'GLOBEX'     # CME电子交易平台
EXCHANGE_IDEALPRO = 'IDEALPRO' # IB外汇ECN

EXCHANGE_CME = 'CME'           # CME交易所
EXCHANGE_ICE = 'ICE'           # ICE交易所
EXCHANGE_LME = 'LME'           # LME交易所

EXCHANGE_OANDA = 'OANDA'       # OANDA外汇做市商
EXCHANGE_OKCOIN = 'OKCOIN'     # OKCOIN比特币交易所
EXCHANGE_HUOBI = 'HUOBI'       # 火币比特币交易所
EXCHANGE_LHANG = 'LHANG'       # 链行比特币交易所

# 货币类型
CURRENCY_USD = 'USD'            # 美元
CURRENCY_CNY = 'CNY'            # 人民币
CURRENCY_HKD = 'HKD'            # 港币
CURRENCY_UNKNOWN = 'UNKNOWN'    # 未知货币
CURRENCY_NONE = ''              # 空货币

# 数据库
LOG_DB_NAME = 'VnTrader_Log_Db'

# 接口类型
GATEWAYTYPE_EQUITY = 'equity'                   # 股票、ETF、债券
GATEWAYTYPE_FUTURES = 'futures'                 # 期货、期权、贵金属
GATEWAYTYPE_INTERNATIONAL = 'international'     # 外盘
GATEWAYTYPE_BTC = 'btc'                         # 比特币
GATEWAYTYPE_DATA = 'data'                       # 数据（非交易）


class GeyaGateway(VtGateway):

    def __init__(self, eventEngine, gatewayName='Geya'):
        """Constructor"""
        super(GeyaGateway, self).__init__(eventEngine, gatewayName)

        self.qryEnabled = False  # 循环查询

        self.api = GeyaApi(self)
        self.rmiIp = EMPTY_STRING
        self.rmiPort = EMPTY_STRING

        self.fileName = self.gatewayName + '_connect.json'
        self.filePath = getJsonPath(self.fileName, __file__)


    def connect(self):
        """连接"""
        try:
            f = file(self.filePath)
        except IOError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = text.LOADING_ERROR
            self.onLog(log)
            return

        # 解析json文件
        setting = json.load(f)
        try:
            self.rmiIp = str(setting['rmiIp'])
            self.rmiPort = str(setting['rmiPort'])
        except KeyError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = text.CONFIG_KEY_MISSING
            self.onLog(log)
            return

        # 初始化接口
        self.api.connect()
        self.writeLog(u'接口初始化成功')

        # 初始化并启动查询
        self.initQuery()
        #self.api.queryPrice()

        # ----------------------------------------------------------------------

    def writeLog(self, content):
        """发出日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.onLog(log)

    # ----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """订阅行情，自动订阅全部行情，无需实现"""
        pass

    def sendOrder(self, orderReq):
        """发单"""
        return self.api.sendOrder(orderReq)

    # ----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.api.exit()

    # ----------------------------------------------------------------------
    def initQuery(self):
        """初始化连续查询"""
        if self.qryEnabled:
            self.qryFunctionList = [self.api.queryAllPrice]
            self.startQuery()

    # ----------------------------------------------------------------------
    def query(self, event):
        """注册到事件处理引擎上的查询函数"""
        for function in self.qryFunctionList:
            function()

    # ----------------------------------------------------------------------
    def startQuery(self):
        """启动连续查询"""
        self.eventEngine.register(EVENT_TIMER, self.query)

    # ----------------------------------------------------------------------
    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled

class GeyaApi(GeyaBase):
    """Constructor"""
    def __init__(self, gateway):
        super(GeyaApi, self).__init__()
        self.gateway  = gateway
        self.gatewayName = gateway.gatewayName

        self.interval = 1

        self.localID = 0  # 本地委托号
        self.localSystemDict = {}  # key:localID, value:systemID
        self.systemLocalDict = {}  # key:systemID, value:localID
        self.workingOrderDict = {}  # key:localID, value:order
        self.reqLocalDict = {}  # key:reqID, value:localID
        self.cancelDict = {}  # key:localID, value:cancelOrderReq

        self.tradeID = 0

        self.tickDict = {}  # key:symbol, value:tick


    # ----------------------------------------------------------------------
    def connect(self):
        """初始化"""
        self.init()

        # 推送合约信息，平盘行情查询接口根据币种和平盘对手确定一条记录
        for counterPartyName in COUNTERPARTYNAME.keys():
            for symbol in SYMBOL_MAP.keys():
                contract = VtContractData()
                contract.gatewayName = self.gatewayName
                contract.symbol = symbol
                #contract.exchange = EXCHANGE_LHANG
                contract.vtSymbol = '.'.join([symbol, counterPartyName])
                #contract.vtSymbol = contract.symbol
                if symbol == SYMBOL_XAUUSD:
                    contract.name = u'黄金美元现货'
                elif symbol == SYMBOL_XAGUSD:
                    contract.name = u'白银美元现货'
                contract.size = 1
                contract.priceTick = 0.01
                contract.productClass = PRODUCT_SPOT
                self.gateway.onContract(contract)

    # ----------------------------------------------------------------------
    def sendOrder(self, req):
        """发单"""
        """发送委托"""
        # 发送限价委托
        #s = SYMBOL_MAP_REVERSE[req.symbol]

        if req.direction == DIRECTION_LONG:
            tradeSide = 'BUY'
        else:
            tradeSide = 'SELL'

        #生成24位流水号，规则：G001+20位流水
        serial = GEYA_PRODUCT_CLASS+datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        reqDate = datetime.datetime.now().strftime('%Y%m%d')
        reqTime = datetime.datetime.now().strftime('%H:%M:%S')
        #req.multiplier 容忍点差
        req.multiplier = '0'
        reqID = self.createOrder(serial, GEYA_PRODUCT_CLASS, req.symbol, reqDate, reqTime, req.volume,
                                 req.lastTradeDateOrContractMonth, tradeSide, req.price, req.multiplier)

        self.localID += 1
        localID = str(self.localID)
        self.reqLocalDict[reqID] = localID

        # 推送委托信息
        order = VtOrderData()
        order.gatewayName = self.gatewayName

        order.symbol = req.symbol
        order.vtSymbol = req.symbol
        #order.exchange = EXCHANGE_LHANG
        #order.vtSymbol = '.'.join([order.symbol, order.exchange])

        #order.orderID = localID
        #order.vtOrderID = '.'.join([order.orderID, order.gatewayName])
        order.orderID = serial
        order.vtOrderID = '.'.join([order.orderID, order.gatewayName])

        order.direction = req.direction
        #order.offset = OFFSET_UNKNOWN
        order.price = req.price
        order.volume = req.volume
        order.orderTime = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        order.status = STATUS_UNKNOWN

        self.workingOrderDict[localID] = order
        self.gateway.onOrder(order)

        # 返回委托号
        return order.vtOrderID

    # ----------------------------------------------------------------------
    def queryPrice(self):
        """查询最优平盘额度"""
        for s in SYMBOL_MAP.keys():
            #self.getDepth(s, self.gateway.rmiIp, self.gateway.rmiPort) #查询平盘全部额度
            for d in TRADE_DIRECTION.keys():
                self.getTicker(s, d, self.gateway.rmiIp, self.gateway.rmiPort) #查询平盘最优额度，考虑买卖方向

    # ----------------------------------------------------------------------
    def queryAllPrice(self):
        """查询全部平盘额度"""
        for s in SYMBOL_MAP.keys():
            self.getDepth(s, self.gateway.rmiIp, self.gateway.rmiPort)

    # ----------------------------------------------------------------------
    def onGetTicker(self, data, req, reqID):
        """查询行情回调"""
        price = data['price'].doubleValue()#平盘价格
        tradeLimitAmount = data['tradeLimitAmount'].doubleValue()#平盘额度
        params = req['params']
        symbol = SYMBOL_MAP[params['symbol']]
        direction = params['direction']

        if symbol not in self.tickDict:
            tick = VtTickData()
            tick.gatewayName = self.gatewayName

            tick.symbol = symbol
            tick.vtSymbol = symbol
            self.tickDict[symbol] = tick
        else:
            tick = self.tickDict[symbol]

        if direction == 'BUY':
            tick.bidPrice1 = price
            tick.bidVolume1 = tradeLimitAmount
            tick.askPrice1 = EMPTY_FLOAT
            tick.askVolume1 = EMPTY_INT
        elif direction == 'SELL':
            tick.askPrice1 = price
            tick.askVolume1 = tradeLimitAmount
            tick.bidPrice1 = EMPTY_FLOAT
            tick.bidVolume1 = EMPTY_INT
        tick.lastPrice = price
        tick.volume = tradeLimitAmount
        tick.exchange = EMPTY_STRING
        tick.openInterest = EMPTY_INT
        tick.time = datetime.datetime.now().strftime('%H%M%S')
        tick.date = datetime.datetime.now().strftime('%Y%m%d')
        tick.openPrice = EMPTY_FLOAT
        tick.highPrice = EMPTY_FLOAT
        tick.lowPrice = EMPTY_FLOAT
        tick.preClosePrice = EMPTY_FLOAT

        tick.upperLimit = EMPTY_FLOAT
        tick.lowerLimit = EMPTY_FLOAT

        self.gateway.onTick(tick)

    # 自动平盘查询全部额度回调，入参data是一个list---------------------------------------
    def onGetDepth(self, data, req, reqID):
        """自动平盘查询全部额度回调"""
        params = req['params']
        symbol = SYMBOL_MAP[params['symbol']]
        if data['resList'].size() == 0:#查询结果为空
            return
        for ele in data['resList']:
            counterPartyName = ele.getCounterPartyName()#平盘对手
            vtSymbol = symbol+"."+counterPartyName#保证唯一性
            if vtSymbol not in self.tickDict:
                tick = VtTickData()
                tick.gatewayName = self.gatewayName
                tick.symbol = symbol
                tick.vtSymbol = vtSymbol
                self.tickDict[symbol] = tick
            else:
                tick = self.tickDict[vtSymbol]

            tick.bidPrice1 =  ele.getBid().doubleValue()
            tick.bidVolume1 = ele.getBidAmount().doubleValue()
            tick.askPrice1 = ele.getAsk().doubleValue()
            tick.askVolume1 = ele.getAskAmount().doubleValue()

            now = datetime.datetime.now()
            tick.time = now.strftime('%H:%M:%S.%f')[:-3]
            tick.date = now.strftime('%Y%m%d')

            tick.askPrice5 = counterPartyName

            self.gateway.onTick(tick)

    # ----------------------------------------------------------------------
    #外汇平盘交易在未指定平盘对手时可能会有多笔成交，data中成交记录可能有
    def onCreateTrade(self, data, req, reqID):
        # 创建报单数据对象
        details = data['details']#自动平盘成交记录
        for ele in details:
            trade = VtTradeData()
            trade.gatewayName = self.gatewayName
            trade.symbol = data['exnm']
            trade.exchange = EMPTY_STRING
            trade.vtSymbol = data['exnm']
            trade.orderID = data['trsn']
            trade.vtOrderID = self.gatewayName+"."+data['trsn']
            trade.direction = data['direction']
            trade.offset = EMPTY_UNICODE
            trade.price = ele.getExpc().doubleValue()
            trade.volume = ele.getLamt().doubleValue()#默认取左头寸，将BigDecimal转化为double在vnpy中没有BigDecimal）以便后续计算
            trade.tradeTime = ele.getTrtm()
            trade.tradeID = data['trsn'] + ele.getPpds() #成交编号规则：委托单号+平盘对手
            self.gateway.onTrade(trade)

    def onCreateOrder(self, data, req, reqID):
        """发单回调"""
        localID = self.reqLocalDict[reqID]
        #systemID = data['id']
        #self.localSystemDict[localID] = systemID
        #self.systemLocalDict[systemID] = localID

        # 撤单
        #if localID in self.cancelDict:
        #    req = self.cancelDict[localID]
        #    self.cancel(req)
        #    del self.cancelDict[localID]

        # 推送委托信息
        order = self.workingOrderDict[localID]
        if data['code'] == '00000':
            order.status = STATUS_NOTTRADED
        self.gateway.onTrade(order)
    def exit(self):
        pass






