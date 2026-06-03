import http from './http'

/** 获取充值档位列表 */
export const getRechargeProducts = () => http.get('/recharge/products')

/** 创建充值订单，返回支付 URL */
export const createRechargeOrder = (data) => http.post('/recharge/create', data)

/** 查询单个订单详情 */
export const getRechargeOrder = (orderId) => http.get(`/recharge/order/${orderId}`)

/** 查询订单列表 */
export const getRechargeOrders = (params) => http.get('/recharge/orders', { params })
