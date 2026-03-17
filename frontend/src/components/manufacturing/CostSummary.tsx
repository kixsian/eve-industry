import React from 'react'
import { CostSummary as CostSummaryData } from '../../api/client'
import styles from './CostSummary.module.css'

interface CostSummaryProps {
  summary: CostSummaryData | null
  productName: string | null
}

export const CostSummary: React.FC<CostSummaryProps> = ({ summary, productName }) => {
  if (!summary) {
    return <div className={styles.empty}>No cost data available</div>
  }

  const profitMargin = summary.margin
  const profitPercent = summary.margin_percent
  const isProfitable = profitMargin > 0

  return (
    <div className={styles.summaryContainer}>
      <div className={styles.summaryGrid}>
        <div className={styles.summaryCard}>
          <label>Material Cost</label>
          <div className={styles.value}>
            ISK {summary.material_cost.toLocaleString()}
          </div>
        </div>

        <div className={styles.summaryCard}>
          <label>Install Cost</label>
          <div className={styles.value}>
            ISK {summary.install_cost.toLocaleString()}
          </div>
        </div>

        <div className={styles.summaryCard}>
          <label>Total Cost</label>
          <div className={`${styles.value} ${styles.totalCost}`}>
            ISK {summary.total_cost.toLocaleString()}
          </div>
        </div>

        <div className={styles.summaryCard}>
          <label>Jita Sell Price</label>
          <div className={styles.value}>
            ISK {summary.jita_sell_price.toLocaleString()}
          </div>
        </div>

        <div className={`${styles.summaryCard} ${isProfitable ? styles.profit : styles.loss}`}>
          <label>Profit Margin</label>
          <div className={styles.value}>
            ISK {Math.abs(profitMargin).toLocaleString()}
          </div>
          <div className={styles.percent}>
            {isProfitable ? '+' : '-'}{Math.abs(profitPercent).toFixed(2)}%
          </div>
        </div>

        <div className={styles.summaryCard}>
          <label>Profit per Unit</label>
          <div className={styles.value}>
            ISK {(profitMargin / (summary.jita_sell_price > 0 ? 1 : 1)).toLocaleString()}
          </div>
        </div>
      </div>

      {summary.material_cost > 0 && (
        <div className={styles.markupSection}>
          <h4>Markup Calculator</h4>
          <div className={styles.markupGrid}>
            <div className={styles.markupOption}>
              <div className={styles.markupLabel}>+10%</div>
              <div className={styles.markupPrice}>
                ISK {(summary.material_cost * 1.1).toLocaleString()}
              </div>
            </div>
            <div className={styles.markupOption}>
              <div className={styles.markupLabel}>+20%</div>
              <div className={styles.markupPrice}>
                ISK {(summary.material_cost * 1.2).toLocaleString()}
              </div>
            </div>
            <div className={styles.markupOption}>
              <div className={styles.markupLabel}>+30%</div>
              <div className={styles.markupPrice}>
                ISK {(summary.material_cost * 1.3).toLocaleString()}
              </div>
            </div>
            <div className={styles.markupOption}>
              <div className={styles.markupLabel}>+50%</div>
              <div className={styles.markupPrice}>
                ISK {(summary.material_cost * 1.5).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
