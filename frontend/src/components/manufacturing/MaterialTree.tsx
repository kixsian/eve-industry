import React, { useState } from 'react'
import { MaterialNode } from '../../api/client'
import styles from './MaterialTree.module.css'

interface MaterialTreeProps {
  tree: MaterialNode | null
}

const MaterialTreeItem: React.FC<{ node: MaterialNode; depth: number }> = ({
  node,
  depth,
}) => {
  const [expanded, setExpanded] = useState(depth === 0)

  const hasChildren = node.children && node.children.length > 0

  return (
    <div className={styles.treeItem} style={{ marginLeft: `${depth * 20}px` }}>
      <div
        className={styles.itemRow}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren && (
          <span className={styles.expandIcon}>{expanded ? '▼' : '▶'}</span>
        )}
        {!hasChildren && <span className={styles.expandIconPlaceholder}></span>}

        <div className={styles.itemInfo}>
          <span className={styles.itemName}>{node.type_name}</span>
          <span className={styles.itemId}>({node.type_id})</span>
        </div>

        <div className={styles.quantities}>
          <span className={styles.quantity}>
            Need: <strong>{node.quantity_needed.toFixed(0)}</strong>
          </span>
          {node.quantity_owned > 0 && (
            <span className={styles.owned}>
              Own: <strong>{node.quantity_owned.toFixed(0)}</strong>
            </span>
          )}
          {node.quantity_to_buy > 0 && (
            <span className={styles.toBuy}>
              Buy: <strong>{node.quantity_to_buy.toFixed(0)}</strong>
            </span>
          )}
        </div>

        <div className={styles.cost}>
          <span className={styles.price}>
            {node.unit_price ? `ISK ${node.unit_price.toLocaleString()}` : 'N/A'}
          </span>
          <span className={styles.total}>
            Total: <strong>ISK {node.total_cost.toLocaleString()}</strong>
          </span>
        </div>
      </div>

      {expanded && hasChildren && (
        <div className={styles.children}>
          {node.children.map((child) => (
            <MaterialTreeItem
              key={child.type_id}
              node={child}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export const MaterialTree: React.FC<MaterialTreeProps> = ({ tree }) => {
  if (!tree) {
    return <div className={styles.empty}>No materials to display</div>
  }

  return (
    <div className={styles.treeContainer}>
      <h3>Material Breakdown</h3>
      <div className={styles.tree}>
        <MaterialTreeItem node={tree} depth={0} />
      </div>
    </div>
  )
}
