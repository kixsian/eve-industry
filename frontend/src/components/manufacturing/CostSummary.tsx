import React from 'react'
import { CostSummary as CostSummaryData } from '../../api/client'
import styles from './CostSummary.module.css'

interface CostSummaryProps {
  summary: CostSummaryData | null
  productName: string | null
}

const MARKUPS = [5, 10, 15, 20, 25, 30]

function formatISK(v: number) {
  if (v >= 1_000_000_000) return (v / 1_000_000_000).toFixed(2) + 'b'
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'm'
  if (v >= 1_000) return (v / 1_000).toFixed(1) + 'k'
  return v.toFixed(0)
}

export const CostSummary: React.FC<CostSummaryProps> = ({ summary, productName }) => {
  if (!summary) {
    return <div className={styles.empty}>No cost data available</div>
  }

  const totalBuildCost = summary.material_cost + summary.install_cost

  return (
    <div className={styles.summaryContainer}>
      <div className={styles.summaryGrid}>
        <div className={styles.summaryCard}>
          <label>Raw Materials</label>
          <div className={styles.value}>{formatISK(summary.material_cost)} ISK</div>
        </div>

        <div className={styles.summaryCard}>
          <label>Buy Components</label>
          <div className={styles.value}>{formatISK(summary.component_buy_cost)} ISK</div>
        </div>

        <div className={styles.summaryCard}>
          <label>Install Cost</label>
          <div className={styles.value}>
            {summary.install_cost > 0 ? formatISK(summary.install_cost) + ' ISK' : '— no system set'}
          </div>
        </div>

        <div className={styles.summaryCard}>
          <label>Total (Raw + Install)</label>
          <div className={`${styles.value} ${styles.totalCost}`}>
            {formatISK(totalBuildCost)} ISK
          </div>
        </div>
      </div>

      <div className={styles.markupSection}>
        <h4>Profit Calculator — {productName}</h4>
        <div className={styles.markupGrid}>
          {MARKUPS.map(pct => {
            const sellPrice = totalBuildCost * (1 + pct / 100)
            const profit = sellPrice - totalBuildCost
            return (
              <div key={pct} className={styles.markupOption}>
                <div className={styles.markupLabel}>+{pct}% markup</div>
                <div className={styles.markupPrice}>{formatISK(sellPrice)} ISK</div>
                <div className={styles.markupProfit}>+{formatISK(profit)} ISK profit</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
