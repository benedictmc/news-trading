// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

extern crate reqwest;
extern crate hex;
extern crate phf;

use models::{BinanceMessage, TradeInfo, TreeOfAlphaTweet, TreeOfAlphaNews, TreeOfAlphaNewsVariation, TradeStats, NewsEvent, Suggestion, BinanceError};
use std::collections::HashMap;
use tokio::time::{Duration, interval, sleep};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use futures::StreamExt;
use futures::SinkExt;
use std::sync::{Arc};
use tokio::sync::Mutex;
use std::fs;
use std::env;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE};
use std::time::{SystemTime, UNIX_EPOCH};
use hmac::{Hmac, Mac, NewMac};
use sha2::Sha256;
use phf::phf_map;


const SYMBOLS: [&str; 213] = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
    "VETUSDT",
    "NEOUSDT",
    "QTUMUSDT",
    "IOSTUSDT",
    "THETAUSDT",
    "ALGOUSDT",
    "ZILUSDT",
    "KNCUSDT",
    "ZRXUSDT",
    "COMPUSDT",
    "OMGUSDT",
    "DOGEUSDT",
    "SXPUSDT",
    "KAVAUSDT",
    "BANDUSDT",
    "RLCUSDT",
    "WAVESUSDT",
    "MKRUSDT",
    "SNXUSDT",
    "DOTUSDT",
    "DEFIUSDT",
    "YFIUSDT",
    "BALUSDT",
    "CRVUSDT",
    "TRBUSDT",
    "RUNEUSDT",
    "SUSHIUSDT",
    "SRMUSDT",
    "EGLDUSDT",
    "SOLUSDT",
    "ICXUSDT",
    "STORJUSDT",
    "BLZUSDT",
    "UNIUSDT",
    "AVAXUSDT",
    "FTMUSDT",
    "HNTUSDT",
    "ENJUSDT",
    "FLMUSDT",
    "TOMOUSDT",
    "RENUSDT",
    "KSMUSDT",
    "NEARUSDT",
    "AAVEUSDT",
    "FILUSDT",
    "RSRUSDT",
    "LRCUSDT",
    "MATICUSDT",
    "OCEANUSDT",
    "CVCUSDT",
    "BELUSDT",
    "CTKUSDT",
    "AXSUSDT",
    "ALPHAUSDT",
    "ZENUSDT",
    "SKLUSDT",
    "GRTUSDT",
    "1INCHUSDT",
    "CHZUSDT",
    "SANDUSDT",
    "ANKRUSDT",
    "BTSUSDT",
    "LITUSDT",
    "UNFIUSDT",
    "REEFUSDT",
    "RVNUSDT",
    "SFPUSDT",
    "XEMUSDT",
    "BTCSTUSDT",
    "COTIUSDT",
    "CHRUSDT",
    "MANAUSDT",
    "ALICEUSDT",
    "HBARUSDT",
    "ONEUSDT",
    "LINAUSDT",
    "STMXUSDT",
    "DENTUSDT",
    "CELRUSDT",
    "HOTUSDT",
    "MTLUSDT",
    "OGNUSDT",
    "NKNUSDT",
    "SCUSDT",
    "DGBUSDT",
    "1000SHIBUSDT",
    "BAKEUSDT",
    "GTCUSDT",
    "BTCDOMUSDT",
    "IOTXUSDT",
    "AUDIOUSDT",
    "RAYUSDT",
    "C98USDT",
    "MASKUSDT",
    "ATAUSDT",
    "DYDXUSDT",
    "1000XECUSDT",
    "GALAUSDT",
    "CELOUSDT",
    "ARUSDT",
    "KLAYUSDT",
    "ARPAUSDT",
    "CTSIUSDT",
    "LPTUSDT",
    "ENSUSDT",
    "PEOPLEUSDT",
    "ANTUSDT",
    "ROSEUSDT",
    "DUSKUSDT",
    "FLOWUSDT",
    "IMXUSDT",
    "API3USDT",
    "GMTUSDT",
    "APEUSDT",
    "WOOUSDT",
    "FTTUSDT",
    "JASMYUSDT",
    "DARUSDT",
    "GALUSDT",
    "OPUSDT",
    "INJUSDT",
    "STGUSDT",
    "FOOTBALLUSDT",
    "SPELLUSDT",
    "1000LUNCUSDT",
    "LUNA2USDT",
    "LDOUSDT",
    "CVXUSDT",
    "ICPUSDT",
    "APTUSDT",
    "QNTUSDT",
    "BLUEBIRDUSDT",
    "FETUSDT",
    "FXSUSDT",
    "HOOKUSDT",
    "MAGICUSDT",
    "TUSDT",
    "RNDRUSDT",
    "HIGHUSDT",
    "MINAUSDT",
    "ASTRUSDT",
    "AGIXUSDT",
    "PHBUSDT",
    "GMXUSDT",
    "CFXUSDT",
    "STXUSDT",
    "COCOSUSDT",
    "BNXUSDT",
    "ACHUSDT",
    "SSVUSDT",
    "CKBUSDT",
    "PERPUSDT",
    "TRUUSDT",
    "LQTYUSDT",
    "USDCUSDT",
    "IDUSDT",
    "ARBUSDT",
    "JOEUSDT",
    "TLMUSDT",
    "AMBUSDT",
    "LEVERUSDT",
    "RDNTUSDT",
    "HFTUSDT",
    "XVSUSDT",
    "BLURUSDT",
    "EDUUSDT",
    "IDEXUSDT",
    "SUIUSDT",
    "1000PEPEUSDT",
    "1000FLOKIUSDT",
    "UMAUSDT",
    "RADUSDT",
    "KEYUSDT",
    "COMBOUSDT",
    "NMRUSDT",
    "MAVUSDT",
    "MDTUSDT",
    "XVGUSDT",
    "WLDUSDT",
    "PENDLEUSDT",
    "ARKMUSDT",
    "AGLDUSDT",
    "YGGUSDT",
    "DODOXUSDT",
    "BNTUSDT",
    "OXTUSDT",
    "SEIUSDT",
    "CYBERUSDT",
    "HIFIUSDT",
    "ARKUSDT",
    "FRONTUSDT",
    "GLMRUSDT",
    "BICOUSDT"
];
static SYMBOL_PRECISION: phf::Map<&'static str, u8> = phf_map! {
    "BTCUSDT" => 3,
    "ETHUSDT" => 3,
    "BCHUSDT" => 3,
    "XRPUSDT" => 1,
    "EOSUSDT" => 1,
    "LTCUSDT" => 3,
    "TRXUSDT" => 0,
    "ETCUSDT" => 2,
    "LINKUSDT" => 2,
    "XLMUSDT" => 0,
    "ADAUSDT" => 0,
    "XMRUSDT" => 3,
    "DASHUSDT" => 3,
    "ZECUSDT" => 3,
    "XTZUSDT" => 1,
    "BNBUSDT" => 2,
    "ATOMUSDT" => 2,
    "ONTUSDT" => 1,
    "IOTAUSDT" => 1,
    "BATUSDT" => 1,
    "VETUSDT" => 0,
    "NEOUSDT" => 2,
    "QTUMUSDT" => 1,
    "IOSTUSDT" => 0,
    "THETAUSDT" => 1,
    "ALGOUSDT" => 1,
    "ZILUSDT" => 0,
    "KNCUSDT" => 0,
    "ZRXUSDT" => 1,
    "COMPUSDT" => 3,
    "OMGUSDT" => 1,
    "DOGEUSDT" => 0,
    "SXPUSDT" => 1,
    "KAVAUSDT" => 1,
    "BANDUSDT" => 1,
    "RLCUSDT" => 1,
    "WAVESUSDT" => 1,
    "MKRUSDT" => 3,
    "SNXUSDT" => 1,
    "DOTUSDT" => 1,
    "DEFIUSDT" => 3,
    "YFIUSDT" => 3,
    "BALUSDT" => 1,
    "CRVUSDT" => 1,
    "TRBUSDT" => 1,
    "RUNEUSDT" => 0,
    "SUSHIUSDT" => 0,
    "SRMUSDT" => 0,
    "EGLDUSDT" => 1,
    "SOLUSDT" => 0,
    "ICXUSDT" => 0,
    "STORJUSDT" => 0,
    "BLZUSDT" => 0,
    "UNIUSDT" => 0,
    "AVAXUSDT" => 0,
    "FTMUSDT" => 0,
    "HNTUSDT" => 0,
    "ENJUSDT" => 0,
    "FLMUSDT" => 0,
    "TOMOUSDT" => 0,
    "RENUSDT" => 0,
    "KSMUSDT" => 1,
    "NEARUSDT" => 0,
    "AAVEUSDT" => 1,
    "FILUSDT" => 1,
    "RSRUSDT" => 0,
    "LRCUSDT" => 0,
    "MATICUSDT" => 0,
    "OCEANUSDT" => 0,
    "CVCUSDT" => 0,
    "BELUSDT" => 0,
    "CTKUSDT" => 0,
    "AXSUSDT" => 0,
    "ALPHAUSDT" => 0,
    "ZENUSDT" => 1,
    "SKLUSDT" => 0,
    "GRTUSDT" => 0,
    "1INCHUSDT" => 0,
    "BTCBUSD" => 3,
    "CHZUSDT" => 0,
    "SANDUSDT" => 0,
    "ANKRUSDT" => 0,
    "BTSUSDT" => 0,
    "LITUSDT" => 1,
    "UNFIUSDT" => 1,
    "REEFUSDT" => 0,
    "RVNUSDT" => 0,
    "SFPUSDT" => 0,
    "XEMUSDT" => 0,
    "BTCSTUSDT" => 1,
    "COTIUSDT" => 0,
    "CHRUSDT" => 0,
    "MANAUSDT" => 0,
    "ALICEUSDT" => 1,
    "HBARUSDT" => 0,
    "ONEUSDT" => 0,
    "LINAUSDT" => 0,
    "STMXUSDT" => 0,
    "DENTUSDT" => 0,
    "CELRUSDT" => 0,
    "HOTUSDT" => 0,
    "MTLUSDT" => 0,
    "OGNUSDT" => 0,
    "NKNUSDT" => 0,
    "SCUSDT" => 0,
    "DGBUSDT" => 0,
    "1000SHIBUSDT" => 0,
    "BAKEUSDT" => 0,
    "GTCUSDT" => 1,
    "ETHBUSD" => 3,
    "BTCDOMUSDT" => 3,
    "BNBBUSD" => 2,
    "ADABUSD" => 0,
    "XRPBUSD" => 1,
    "IOTXUSDT" => 0,
    "DOGEBUSD" => 0,
    "AUDIOUSDT" => 0,
    "RAYUSDT" => 1,
    "C98USDT" => 0,
    "MASKUSDT" => 0,
    "ATAUSDT" => 0,
    "SOLBUSD" => 0,
    "FTTBUSD" => 1,
    "DYDXUSDT" => 1,
    "1000XECUSDT" => 0,
    "GALAUSDT" => 0,
    "CELOUSDT" => 1,
    "ARUSDT" => 1,
    "KLAYUSDT" => 1,
    "ARPAUSDT" => 0,
    "CTSIUSDT" => 0,
    "LPTUSDT" => 1,
    "ENSUSDT" => 1,
    "PEOPLEUSDT" => 0,
    "ANTUSDT" => 1,
    "ROSEUSDT" => 0,
    "DUSKUSDT" => 0,
    "FLOWUSDT" => 1,
    "IMXUSDT" => 0,
    "API3USDT" => 1,
    "GMTUSDT" => 0,
    "APEUSDT" => 0,
    "WOOUSDT" => 0,
    "FTTUSDT" => 1,
    "JASMYUSDT" => 0,
    "DARUSDT" => 1,
    "GALUSDT" => 0,
    "AVAXBUSD" => 1,
    "NEARBUSD" => 1,
    "GMTBUSD" => 1,
    "APEBUSD" => 1,
    "GALBUSD" => 0,
    "FTMBUSD" => 0,
    "DODOBUSD" => 0,
    "ANCBUSD" => 0,
    "GALABUSD" => 0,
    "TRXBUSD" => 0,
    "1000LUNCBUSD" => 0,
    "OPUSDT" => 1,
    "DOTBUSD" => 1,
    "TLMBUSD" => 0,
    "WAVESBUSD" => 1,
    "LINKBUSD" => 1,
    "SANDBUSD" => 1,
    "LTCBUSD" => 2,
    "MATICBUSD" => 0,
    "CVXBUSD" => 1,
    "FILBUSD" => 1,
    "1000SHIBBUSD" => 0,
    "LEVERBUSD" => 0,
    "ETCBUSD" => 1,
    "LDOBUSD" => 1,
    "UNIBUSD" => 1,
    "AUCTIONBUSD" => 1,
    "INJUSDT" => 1,
    "STGUSDT" => 0,
    "SPELLUSDT" => 0,
    "1000LUNCUSDT" => 0,
    "LUNA2USDT" => 0,
    "AMBBUSD" => 0,
    "PHBBUSD" => 0,
    "LDOUSDT" => 0,
    "CVXUSDT" => 0,
    "ICPUSDT" => 0,
    "APTUSDT" => 1,
    "QNTUSDT" => 1,
    "APTBUSD" => 1,
    "BLUEBIRDUSDT" => 1,
    "FETUSDT" => 0,
    "AGIXBUSD" => 0,
    "FXSUSDT" => 1,
    "HOOKUSDT" => 1,
    "MAGICUSDT" => 1,
    "TUSDT" => 0,
    "RNDRUSDT" => 1,
    "HIGHUSDT" => 1,
    "MINAUSDT" => 0,
    "ASTRUSDT" => 0,
    "AGIXUSDT" => 0,
    "PHBUSDT" => 0,
    "GMXUSDT" => 2,
    "CFXUSDT" => 0,
    "STXUSDT" => 0,
    "COCOSUSDT" => 1,
    "BNXUSDT" => 1,
    "ACHUSDT" => 0,
    "SSVUSDT" => 2,
    "CKBUSDT" => 0,
    "PERPUSDT" => 1,
    "TRUUSDT" => 0,
    "LQTYUSDT" => 1,
    "USDCUSDT" => 0,
    "IDUSDT" => 0,
    "ARBUSDT" => 1,
    "JOEUSDT" => 0,
    "TLMUSDT" => 0,
    "AMBUSDT" => 0,
    "LEVERUSDT" => 0,
    "RDNTUSDT" => 0,
    "HFTUSDT" => 0,
    "XVSUSDT" => 1,
    "ETHBTC" => 2,
    "BLURUSDT" => 0,
    "EDUUSDT" => 0,
    "IDEXUSDT" => 0,
    "SUIUSDT" => 1,
    "1000PEPEUSDT" => 0,
    "1000FLOKIUSDT" => 0,
    "UMAUSDT" => 0,
    "RADUSDT" => 0,
    "KEYUSDT" => 0,
    "COMBOUSDT" => 1,
    "NMRUSDT" => 1,
    "MDTUSDT" => 0,
    "XVGUSDT" => 0,
    "WLDUSDT" => 0,
    "PENDLEUSDT" => 0,
    "ARKMUSDT" => 0,
    "AGLDUSDT" => 0,
    "YGGUSDT" => 0,
    "DODOXUSDT" => 0
}; 
static SYMBOL_PRICE_PRECISION: phf::Map<&'static str, u8> = phf_map! {
    "BTCUSDT" => 2,
    "ETHUSDT" => 2,
    "BCHUSDT" => 2,
    "XRPUSDT" => 4,
    "EOSUSDT" => 3,
    "LTCUSDT" => 2,
    "TRXUSDT" => 5,
    "ETCUSDT" => 3,
    "LINKUSDT" => 3,
    "XLMUSDT" => 5,
    "ADAUSDT" => 5,
    "XMRUSDT" => 2,
    "DASHUSDT" => 2,
    "ZECUSDT" => 2,
    "XTZUSDT" => 3,
    "BNBUSDT" => 3,
    "ATOMUSDT" => 3,
    "ONTUSDT" => 4,
    "IOTAUSDT" => 4,
    "BATUSDT" => 4,
    "VETUSDT" => 6,
    "NEOUSDT" => 3,
    "QTUMUSDT" => 3,
    "IOSTUSDT" => 6,
    "THETAUSDT" => 4,
    "ALGOUSDT" => 4,
    "ZILUSDT" => 5,
    "KNCUSDT" => 5,
    "ZRXUSDT" => 4,
    "COMPUSDT" => 2,
    "OMGUSDT" => 4,
    "DOGEUSDT" => 6,
    "SXPUSDT" => 4,
    "KAVAUSDT" => 4,
    "BANDUSDT" => 4,
    "RLCUSDT" => 4,
    "WAVESUSDT" => 4,
    "MKRUSDT" => 2,
    "SNXUSDT" => 3,
    "DOTUSDT" => 3,
    "DEFIUSDT" => 1,
    "YFIUSDT" => 1,
    "BALUSDT" => 3,
    "CRVUSDT" => 3,
    "TRBUSDT" => 3,
    "RUNEUSDT" => 4,
    "SUSHIUSDT" => 4,
    "SRMUSDT" => 4,
    "EGLDUSDT" => 3,
    "SOLUSDT" => 4,
    "ICXUSDT" => 4,
    "STORJUSDT" => 4,
    "BLZUSDT" => 5,
    "UNIUSDT" => 4,
    "AVAXUSDT" => 4,
    "FTMUSDT" => 6,
    "HNTUSDT" => 4,
    "ENJUSDT" => 5,
    "FLMUSDT" => 4,
    "TOMOUSDT" => 4,
    "RENUSDT" => 5,
    "KSMUSDT" => 3,
    "NEARUSDT" => 4,
    "AAVEUSDT" => 3,
    "FILUSDT" => 3,
    "RSRUSDT" => 6,
    "LRCUSDT" => 5,
    "MATICUSDT" => 5,
    "OCEANUSDT" => 5,
    "CVCUSDT" => 5,
    "BELUSDT" => 5,
    "CTKUSDT" => 5,
    "AXSUSDT" => 5,
    "ALPHAUSDT" => 5,
    "ZENUSDT" => 3,
    "SKLUSDT" => 5,
    "GRTUSDT" => 5,
    "1INCHUSDT" => 4,
    "BTCBUSD" => 1,
    "CHZUSDT" => 5,
    "SANDUSDT" => 5,
    "ANKRUSDT" => 6,
    "BTSUSDT" => 5,
    "LITUSDT" => 3,
    "UNFIUSDT" => 3,
    "REEFUSDT" => 6,
    "RVNUSDT" => 5,
    "SFPUSDT" => 4,
    "XEMUSDT" => 4,
    "BTCSTUSDT" => 3,
    "COTIUSDT" => 5,
    "CHRUSDT" => 4,
    "MANAUSDT" => 4,
    "ALICEUSDT" => 3,
    "HBARUSDT" => 5,
    "ONEUSDT" => 5,
    "LINAUSDT" => 5,
    "STMXUSDT" => 5,
    "DENTUSDT" => 6,
    "CELRUSDT" => 5,
    "HOTUSDT" => 6,
    "MTLUSDT" => 4,
    "OGNUSDT" => 4,
    "NKNUSDT" => 5,
    "SCUSDT" => 6,
    "DGBUSDT" => 5,
    "1000SHIBUSDT" => 6,
    "BAKEUSDT" => 4,
    "GTCUSDT" => 3,
    "ETHBUSD" => 2,
    "BTCDOMUSDT" => 1,
    "BNBBUSD" => 3,
    "ADABUSD" => 5,
    "XRPBUSD" => 4,
    "IOTXUSDT" => 5,
    "DOGEBUSD" => 6,
    "AUDIOUSDT" => 4,
    "RAYUSDT" => 3,
    "C98USDT" => 4,
    "MASKUSDT" => 4,
    "ATAUSDT" => 4,
    "SOLBUSD" => 4,
    "FTTBUSD" => 3,
    "DYDXUSDT" => 3,
    "1000XECUSDT" => 5,
    "GALAUSDT" => 5,
    "CELOUSDT" => 3,
    "ARUSDT" => 3,
    "KLAYUSDT" => 4,
    "ARPAUSDT" => 5,
    "CTSIUSDT" => 4,
    "LPTUSDT" => 3,
    "ENSUSDT" => 3,
    "PEOPLEUSDT" => 5,
    "ANTUSDT" => 3,
    "ROSEUSDT" => 5,
    "DUSKUSDT" => 5,
    "FLOWUSDT" => 3,
    "IMXUSDT" => 4,
    "API3USDT" => 4,
    "GMTUSDT" => 5,
    "APEUSDT" => 4,
    "WOOUSDT" => 5,
    "FTTUSDT" => 4,
    "JASMYUSDT" => 6,
    "DARUSDT" => 4,
    "GALUSDT" => 5,
    "AVAXBUSD" => 6,
    "NEARBUSD" => 7,
    "GMTBUSD" => 7,
    "APEBUSD" => 7,
    "GALBUSD" => 7,
    "FTMBUSD" => 7,
    "DODOBUSD" => 7,
    "ANCBUSD" => 7,
    "GALABUSD" => 7,
    "TRXBUSD" => 7,
    "1000LUNCBUSD" => 7,
    "OPUSDT" => 7,
    "DOTBUSD" => 7,
    "TLMBUSD" => 7,
    "WAVESBUSD" => 7,
    "LINKBUSD" => 7,
    "SANDBUSD" => 7,
    "LTCBUSD" => 6,
    "MATICBUSD" => 7,
    "CVXBUSD" => 7,
    "FILBUSD" => 7,
    "1000SHIBBUSD" => 7,
    "LEVERBUSD" => 7,
    "ETCBUSD" => 6,
    "LDOBUSD" => 6,
    "UNIBUSD" => 6,
    "AUCTIONBUSD" => 7,
    "INJUSDT" => 6,
    "STGUSDT" => 7,
    "SPELLUSDT" => 7,
    "1000LUNCUSDT" => 7,
    "LUNA2USDT" => 7,
    "AMBBUSD" => 7,
    "PHBBUSD" => 7,
    "LDOUSDT" => 6,
    "CVXUSDT" => 6,
    "ICPUSDT" => 6,
    "APTUSDT" => 5,
    "QNTUSDT" => 6,
    "APTBUSD" => 5,
    "BLUEBIRDUSDT" => 5,
    "FETUSDT" => 7,
    "AGIXBUSD" => 7,
    "FXSUSDT" => 6,
    "HOOKUSDT" => 6,
    "MAGICUSDT" => 6,
    "TUSDT" => 7,
    "RNDRUSDT" => 6,
    "HIGHUSDT" => 6,
    "MINAUSDT" => 7,
    "ASTRUSDT" => 7,
    "AGIXUSDT" => 7,
    "PHBUSDT" => 7,
    "GMXUSDT" => 6,
    "CFXUSDT" => 7,
    "STXUSDT" => 7,
    "COCOSUSDT" => 6,
    "BNXUSDT" => 6,
    "ACHUSDT" => 7,
    "SSVUSDT" => 6,
    "CKBUSDT" => 7,
    "PERPUSDT" => 6,
    "TRUUSDT" => 7,
    "LQTYUSDT" => 6,
    "USDCUSDT" => 7,
    "IDUSDT" => 7,
    "ARBUSDT" => 6,
    "JOEUSDT" => 7,
    "TLMUSDT" => 7,
    "AMBUSDT" => 7,
    "LEVERUSDT" => 7,
    "RDNTUSDT" => 7,
    "HFTUSDT" => 7,
    "XVSUSDT" => 6,
    "ETHBTC" => 6,
    "BLURUSDT" => 7,
    "EDUUSDT" => 7,
    "IDEXUSDT" => 7,
    "SUIUSDT" => 6,
    "1000PEPEUSDT" => 7,
    "1000FLOKIUSDT" => 7,
    "UMAUSDT" => 6,
    "RADUSDT" => 6,
    "KEYUSDT" => 7,
    "COMBOUSDT" => 6,
    "NMRUSDT" => 6,
    "BTCUSDT_230929" => 1,
    "MDTUSDT" => 7,
    "XVGUSDT" => 7,
    "WLDUSDT" => 7,
    "PENDLEUSDT" => 7,
    "ARKMUSDT" => 7,
    "AGLDUSDT" => 7,
    "YGGUSDT" => 7,
    "DODOXUSDT" => 7
};

const BINANCE_TICK_INTERVAL: u64 = 1;
const TOA_PING_INTERVAL: u64 = 20;


#[tokio::main]
async fn main() {
    // Run both WebSocket tasks concurrently
    println!("> Starting WebSocket tasks...");
    
    let symbol_trade_infos = Arc::new(Mutex::new(HashMap::new()));
    let symbol_trade_stats = Arc::new(Mutex::new(HashMap::new()));
    let news_event_log = Arc::new(Mutex::new(HashMap::new()));

    for &symbol in SYMBOLS.iter() {
        symbol_trade_infos.lock().await.insert(symbol.to_string(), TradeInfo::default());
        symbol_trade_stats.lock().await.insert(symbol.to_string(), TradeStats::default());
    }
    tokio::spawn(focus_new_event_log(news_event_log.clone(), symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::spawn(calculate_averages(symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::join!(run_binance_websocket(symbol_trade_infos.clone()), run_treeofalpha_websocket(news_event_log.clone()));
}


async fn run_binance_websocket(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>) {

    let symbols_string = SYMBOLS.iter()
        .map(|s| format!("{}@aggTrade", s.to_lowercase()))
        .collect::<Vec<_>>()
        .join("/");

    let url_str = format!("wss://stream.binance.com:443/stream?streams={}", symbols_string);
    let url = Url::parse(&url_str).unwrap();

    let (mut ws_stream, response) = connect_async(url).await.expect("Failed to connect");

    println!("Connected with response: {:?}", response);

    let (mut sink, mut stream) = ws_stream.split();

    let mut interval_tick = interval(Duration::from_secs(60));

    loop {
        tokio::select! {
            Some(Ok(message)) = stream.next() => {
                match message {
                    Message::Ping(ping_data) => {
                        if let Err(e) = sink.send(Message::Pong(ping_data)).await {
                            eprintln!("Failed to send pong: {}", e);
                            // Optionally, reconnect logic here
                        }
                    },
                    Message::Text(text) => {
                        // Handle text messages as before
                        match serde_json::from_str::<BinanceMessage>(&text) {
                            Ok(parsed_message) => {
                                let symbol = parsed_message.data.s;
                                let mut trade_info_lock = symbol_trade_infos.lock().await;
        
                                if let Some(trade_info) = trade_info_lock.get_mut(&symbol) {
                                    trade_info.count += 1;
                                    if let (Ok(price), Ok(qty)) = (parsed_message.data.p.parse::<f64>(), parsed_message.data.q.parse::<f64>()) {
        
                                        trade_info.total_price += price;
                                        let volume = price * qty;
                                        if parsed_message.data.m {
                                            trade_info.volume_sold += volume;
                                            trade_info.amount_of_sells += 1;
                                        } else {
                                            trade_info.volume_bought += volume;
                                            trade_info.amount_of_buys += 1;
                                        }
                                    }
                                }
                            },
                            Err(e) => eprintln!("Failed to deserialize message: {}, text: {}", e, text),
                        }
                    },
                    _ => eprintln!("Received unexpected message: {:?}", message),
                }
            }
        }
    }
}


async fn run_treeofalpha_websocket(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>) {
    let url = Url::parse("wss://news.treeofalpha.com/ws").unwrap();

    loop {
        match connect_async(url.clone()).await {
            Ok((ws_stream, response)) => {
                println!("Connected to treeofalpha with response: {:?}", response);

                let (mut ws_write, mut ws_read) = ws_stream.split();
                let mut interval_tick = interval(Duration::from_secs(TOA_PING_INTERVAL));

                loop {
                    tokio::select! {
                        Some(Ok(message)) = ws_read.next() => {
                            match message {
                                Message::Text(text) => {
                                    let current_time = get_current_time();
                                    match serde_json::from_str::<TreeOfAlphaNews>(&text) {
                                        Ok(news_message) => {
                                            println!("> treeofalpha: Received news at {}", current_time);
                                            println!("> treeofalpha: Title {}", news_message.title );

                                            process_suggestions(&news_message.suggestions, &news_event_log, &news_message.title).await;
                                        },
                                        Err(_) => {
                                            match serde_json::from_str::<TreeOfAlphaNewsVariation>(&text) {
                                                Ok(news_variation_message) => {
                                                   
                                                    println!("> treeofalpha: Received news variation at {}", current_time);
                                                    println!("> treeofalpha: Title {}", news_variation_message.title );
        
                                                    process_suggestions(&news_variation_message.suggestions, &news_event_log, &news_variation_message.title).await;
                                                },
                                                Err(_) => {
                                                    match serde_json::from_str::<TreeOfAlphaTweet>(&text) {
                                                        Ok(tweet_message) => {
                                                            println!("> treeofalpha: Received tweet at {}", current_time);
                                                            println!("> treeofalpha: Title {}", tweet_message.title );
                                                            println!("> treeofalpha: Body {}", tweet_message.body );

                                                            process_suggestions(&tweet_message.suggestions, &news_event_log, &tweet_message.body).await;
                                                        },
                                                        Err(e) => {
                                                            println!("> treeofalpha: Failed to deserialize both formats: {} {}", e, text);
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                Message::Pong(_) => {
                                    // No message for now
                                },
                                _ => {}
                            }
                        },
                        _ = interval_tick.tick() => {
                            match ws_write.send(Message::Ping(Vec::new())).await {
                                Ok(_) => {},
                                Err(e) => {
                                    println!("> treeofalpha: Failed to send ping to treeofalpha: {}", e);
                                    break;  // Break inner loop to trigger reconnection
                                },
                            }
                        },
                    }
                }
            },
            Err(e) => {
                println!("Failed to connect to treeofalpha: {}", e);
            },
        }

        println!("Attempting to reconnect in 5 seconds...");
        sleep(Duration::from_secs(5)).await;  // Wait for 5 seconds before attempting to reconnect
    }
}


async fn calculate_averages(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;
        let mut symbol_trade_infos_lock = symbol_trade_infos.lock().await;

        for (symbol, trade_info) in symbol_trade_infos_lock.iter_mut() {
            
            let mut trade_stats_lock = symbol_trade_stats.lock().await;

            if let Some(trade_stats) = trade_stats_lock.get_mut(symbol) {
                trade_stats.amount_of_buys.update(trade_info.amount_of_buys);
                trade_stats.amount_of_sells.update(trade_info.amount_of_sells);
                trade_stats.volume_sold.update(trade_info.volume_sold);
                trade_stats.volume_bought.update(trade_info.volume_bought);
            }
        }
        symbol_trade_infos_lock.values_mut().for_each(|info| *info = TradeInfo::default());
    }
}

async fn focus_new_event_log(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>, symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_millis(500));

    loop {
        interval.tick().await;

        let mut news_event_log_lock = news_event_log.lock().await;

        if news_event_log_lock.is_empty() {
            continue;
        }

        let mut events_to_remove = Vec::new();

        let current_time = get_current_time();

        for (binance_symbol, news_event) in news_event_log_lock.iter_mut() {

            if news_event.time_to_end < current_time {
                events_to_remove.push(binance_symbol.clone());
                continue;
            }

            let symbol_trade_infos_lock = symbol_trade_infos.lock().await;

            if let Some(latest_trade_info) = symbol_trade_infos_lock.get(binance_symbol) {

                let mut trade_stats_lock = symbol_trade_stats.lock().await;

                if let Some(trade_stats) = trade_stats_lock.get_mut(binance_symbol) {
                    let current_price = latest_trade_info.total_price / latest_trade_info.count as f64;


                    if !current_price.is_nan() {
                        if news_event.start_price == 0.0{
                            news_event.start_price = current_price.clone();
                            println!("start_price set " )
                        }
                                
                        let price_diff = (current_price - news_event.start_price) / news_event.start_price ;

                        if price_diff > news_event.max_price_diff_pos {
                            news_event.max_price_diff_pos = price_diff.clone();
                        }

                        if price_diff < news_event.max_price_diff_neg {
                            news_event.max_price_diff_neg = price_diff.clone();
                        }
                    }
                    let amount_of_buys_z_score = trade_stats.amount_of_buys.z_score(latest_trade_info.amount_of_buys);
                    let amount_of_sells_z_score = trade_stats.amount_of_sells.z_score(latest_trade_info.amount_of_sells);
                    let volume_sold_z_score = trade_stats.volume_sold.z_score(latest_trade_info.volume_sold);
                    let volume_bought_z_score = trade_stats.volume_bought.z_score(latest_trade_info.volume_bought);

                    let total_zscore = amount_of_buys_z_score + amount_of_sells_z_score + volume_sold_z_score + volume_bought_z_score;

                    if total_zscore > news_event.max_z_score {
                        news_event.max_z_score = total_zscore.clone();
                    }

                    if total_zscore > 10.0{
                        println!("*******");
                        println!("> focus_new_event_log: binance_symbol: {}", binance_symbol);
                        println!("> focus_new_event_log: News event title {}", news_event.news_title);    
                        println!("> focus_new_event_log: total_zscore: {}", total_zscore);
                        println!("*******");
                    }

                    if total_zscore > 100.0{

                        println!("*******");
                        println!("> focus_new_event_log: binance_symbol: {}", binance_symbol);
                        println!("> focus_new_event_log: News event title {}", news_event.news_title);
                        println!("> focus_new_event_log: GOING TO TRADE!!");
                        println!("> focus_new_event_log: Time is {}", get_current_time());

                        let price_precision = match SYMBOL_PRICE_PRECISION.get(&binance_symbol) {
                            Some(&value) => value,
                            None => 4,
                        } as u32;
                    
                        println!("> focus_new_event_log: Precision of {}: {}", &binance_symbol, price_precision);

                        let trade_price = round(latest_trade_info.total_price / latest_trade_info.count as f64, price_precision);
                        let trade_direction = if trade_price < news_event.start_price { "SELL" } else { "BUY" };
                        
                        println!("> focus_new_event_log: trade_direction: {}", &trade_direction);
                        println!("> focus_new_event_log: trade_price: {}", &trade_price);

                        let sl_price = if trade_direction == "SELL" {round(trade_price * 1.02, price_precision)} else { round(trade_price * 0.98, price_precision) };
                        let tp_price = if trade_direction == "SELL" {round(trade_price * 0.95, price_precision)} else { round(trade_price * 1.05, price_precision) };

                        println!("> focus_new_event_log: sl_price: {}", &sl_price);
                        println!("> focus_new_event_log: tp_price: {}", &tp_price);

                        send_futures_order(binance_symbol, trade_direction, "LIMIT",  200.0, trade_price, 5, sl_price, tp_price).await;
                        std::process::exit(1);  // Exit the program
                    }
                }
            }
        }

        drop(news_event_log_lock);
        let mut news_event_log_lock = news_event_log.lock().await;

        for key in events_to_remove {
            println!("> focus_new_event_log: Removing key: {}", key);

            if let Some(news_event) = news_event_log_lock.get_mut(&key){
                println!("> focus_new_event_log: Saving news event to file");
                // save_news_event_to_file(news_event).await;
            }
            news_event_log_lock.remove(&key);
        }
    }
}

async fn process_suggestions(suggestions: &[Suggestion], news_event_log: &Arc<Mutex<HashMap<String, NewsEvent>>>, title: &str) {
    for suggestion in suggestions {
        for symbols in &suggestion.symbols {
            if symbols.get("exchange") == Some(&"binance-futures".to_string()) {
                if let Some(exchange_symbol) = symbols.get("symbol") {
                    let binance_symbol = exchange_symbol.to_string();
                    let mut lock = news_event_log.lock().await;
                    if let Some(news_event) = lock.get_mut(&binance_symbol) {
                        news_event.news_occurance += 1;
                        news_event.time_to_end = get_current_time() + 60000000000 // Plus 1 minutes;
                    } else {
                        let news_event = NewsEvent {
                            binance_symbol: binance_symbol.clone(),
                            time_started: get_current_time(),
                            news_occurance: 1,
                            news_title: title.to_string(),
                            time_to_end: get_current_time() + 60000000000, // Plus 1 minutes
                            start_price: 0.0,
                            max_price_diff_neg: 100.0,
                            max_price_diff_pos: 0.0,
                            max_z_score: 0.0,
                        };
                        lock.insert(binance_symbol, news_event);
                    }
                }
            }
        }
    }
}


//  Helper functions
fn round(x: f64, decimals: u32) -> f64 {
    let y = 10i64.pow(decimals) as f64;
    (x * y).round() / y
}

fn get_current_time() -> u128 {
    SystemTime::now()
    .duration_since(SystemTime::UNIX_EPOCH)
    .unwrap()
    .as_nanos()
}

async fn save_news_event_to_file(news_event: &NewsEvent) -> Result<(), Box<dyn std::error::Error>> {
    // Serialize the struct to a JSON string
    let time_started = news_event.time_started;
    let binance_symbol = news_event.binance_symbol.clone();

    let json = serde_json::to_string_pretty(news_event)?;
    let file_path = format!("news_events/{}{}.json", time_started, binance_symbol);
    // Write the JSON string to a file
    fs::write(file_path, json)?;

    Ok(())
}

async fn send_futures_order(
    symbol: &str,
    side: &str,
    type_: &str,
    quantity: f64,
    price: f64,
    leverage: i32,
    stop_loss_price: f64,
    take_profit_price: f64,
) -> Result<(), reqwest::Error> {

    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");
    
    // To change leverage
    let leverage_result = change_leverage(&symbol, leverage).await;

    if let Err(e) = leverage_result {
        eprintln!("Failed to change leverage: {}", e);
        return Err(e);
    }

    let opposite_side = if side == "BUY" { "SELL" } else { "BUY" };

    let precision = match SYMBOL_PRECISION.get(&symbol) {
        Some(&value) => value,
        None => 2,
    } as u32;

    println!("> send_futures_order: Current Time: {}", get_current_time());
    println!("> send_futures_order: Percision: {}", precision);

    let symbol_amount = round((quantity / price)*leverage as f64, precision);

    println!("> send_futures_order: symbol_amount: {}", symbol_amount);
    
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();

    let params = format!(
        "symbol={}&side={}&type={}&quantity={}&price={}&timeInForce=GTC&timestamp={}",
        symbol, side, type_, symbol_amount, price, timestamp
    );
    submit_trade(&params).await;


    let stop_loss_params = format!(
        "symbol={}&side={}&type=STOP_MARKET&quantity={:.2}&stopPrice={:.2}&timeInForce=GTC&timestamp={}",
        symbol, opposite_side, symbol_amount, stop_loss_price, timestamp
    );
    submit_trade(&stop_loss_params).await;


    // let take_profit_params = format!(
    //     "symbol={}&side={}&type=TAKE_PROFIT_MARKET&quantity={:.2}&stopPrice={:.2}&timeInForce=GTC&timestamp={}",
    //     symbol, opposite_side, symbol_amount, take_profit_price, timestamp
    // );
    // submit_trade(&take_profit_params).await;

    Ok(())
}


async fn change_leverage(symbol: &str, leverage: i32) -> Result<(), reqwest::Error> {
    let client = reqwest::Client::new();

    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");

    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();

    // Change the leverage to 5x
    let leverage_params = format!("symbol={}&leverage={}&timestamp={}", symbol, leverage, timestamp);
    let leverage_signature = get_signature(&api_secret, &leverage_params);

    let mut headers = HeaderMap::new();
    headers.insert("X-MBX-APIKEY", HeaderValue::from_str(&api_key).unwrap());
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/x-www-form-urlencoded"));

    let change_leverage_url = format!("https://fapi.binance.com/fapi/v1/leverage?{}&signature={}", leverage_params, leverage_signature);

    let change_leverage_response = client.post(&change_leverage_url).headers(headers).send().await?;

    // Check for errors in the response
    if change_leverage_response.status().is_success() {
        println!("Leverage changed successfully");
        Ok(())
    } else {
        // Output the error message from Binance
        let error_msg: BinanceError = change_leverage_response.json().await?;
        println!("Failed to change leverage: {}", error_msg.msg);
        Ok(())
    }
}


async fn submit_trade(params: &str) -> Result<(), reqwest::Error>{
    let client = reqwest::Client::new();
    
    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");
   
    let signature = get_signature(&api_secret, &params);

    println!("> submit_trade: signature: {}", signature);

    let mut headers = HeaderMap::new();
    headers.insert("X-MBX-APIKEY", HeaderValue::from_str(&api_key).unwrap());
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/x-www-form-urlencoded"));
    
    let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", params, signature);
    println!("url: {}", url);
    
    let response = client.post(&url).headers(headers).send().await?;
    
    if response.status().is_success() {
        println!("> submit_trade: Order placed successfully");
    } else {
        // The request failed, print the error message
        let error_text = response.text().await?;
        println!("> submit_trade: Error: {}", error_text);
    }

    Ok(())
}


fn get_signature(api_secret: &str, request: &str) -> String {
    let mut signed_key = Hmac::<Sha256>::new_from_slice(api_secret.as_bytes()).unwrap();
    signed_key.update(request.as_bytes());
    let signature = hex::encode(signed_key.finalize().into_bytes());
    signature
}
