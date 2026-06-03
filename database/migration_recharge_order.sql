-- 充值订单表
-- 记录用户发起的每一笔充值，由支付宝异步通知驱动状态变更
CREATE TABLE IF NOT EXISTS t_recharge_order (
  id BIGINT NOT NULL PRIMARY KEY COMMENT '雪花ID',
  order_no VARCHAR(32) NOT NULL COMMENT '商户订单号（唯一，传给支付宝作为 out_trade_no）',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  product_id INT NOT NULL COMMENT '充值档位ID，对应 recharge_products 配置',
  amount DECIMAL(10, 2) NOT NULL COMMENT '支付金额（元）',
  credits INT NOT NULL COMMENT '基础积分数',
  bonus_credits INT NOT NULL DEFAULT 0 COMMENT '赠送积分数',
  total_credits INT NOT NULL COMMENT '到账总积分（credits + bonus_credits）',
  trade_no VARCHAR(64) NOT NULL DEFAULT '' COMMENT '支付宝交易号（异步通知时回填）',
  status TINYINT NOT NULL DEFAULT 0 COMMENT '订单状态：0-待支付 1-已支付 2-已关闭',
  credits_granted TINYINT NOT NULL DEFAULT 0 COMMENT '积分是否已发放：0-未发放 1-已发放',
  pay_channel VARCHAR(10) NOT NULL DEFAULT 'page' COMMENT '支付渠道：page-PC网站 wap-手机网站',
  pay_time DATETIME NULL COMMENT '支付完成时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY uk_order_no (order_no),
  INDEX idx_user_id (user_id),
  INDEX idx_status_granted (status, credits_granted),
  INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='充值订单表';
