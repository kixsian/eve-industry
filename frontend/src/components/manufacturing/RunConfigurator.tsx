import React from 'react'
import styles from './RunConfigurator.module.css'

interface RunConfiguratorProps {
  runs: number
  meLevel: number
  structureBonus: number
  rigBonus: number
  buildIntermediates: boolean
  onRunsChange: (runs: number) => void
  onMeLevelChange: (me: number) => void
  onStructureBonusChange: (bonus: number) => void
  onRigBonusChange: (bonus: number) => void
  onBuildIntermediatesChange: (build: boolean) => void
}

export const RunConfigurator: React.FC<RunConfiguratorProps> = ({
  runs,
  meLevel,
  structureBonus,
  rigBonus,
  buildIntermediates,
  onRunsChange,
  onMeLevelChange,
  onStructureBonusChange,
  onRigBonusChange,
  onBuildIntermediatesChange,
}) => {
  return (
    <div className={styles.configurator}>
      <div className={styles.configGrid}>
        <div className={styles.configGroup}>
          <label htmlFor="runs">Runs</label>
          <input
            id="runs"
            type="number"
            min="1"
            max="10000"
            value={runs}
            onChange={(e) => onRunsChange(Math.max(1, parseInt(e.target.value) || 1))}
            className={styles.input}
          />
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="meLevel">
            Material Efficiency (ME)
            <span className={styles.hint}> 0-10</span>
          </label>
          <div className={styles.meSlider}>
            <input
              id="meLevel"
              type="range"
              min="0"
              max="10"
              value={meLevel}
              onChange={(e) => onMeLevelChange(parseInt(e.target.value))}
              className={styles.slider}
            />
            <span className={styles.meValue}>{meLevel}</span>
          </div>
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="structureBonus">
            Structure Bonus
            <span className={styles.hint}> EC=0.01</span>
          </label>
          <input
            id="structureBonus"
            type="number"
            min="0"
            max="0.1"
            step="0.001"
            value={structureBonus}
            onChange={(e) => onStructureBonusChange(parseFloat(e.target.value) || 0)}
            className={styles.input}
          />
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="rigBonus">
            Rig Bonus
            <span className={styles.hint}> T1=0.02</span>
          </label>
          <input
            id="rigBonus"
            type="number"
            min="0"
            max="0.1"
            step="0.001"
            value={rigBonus}
            onChange={(e) => onRigBonusChange(parseFloat(e.target.value) || 0)}
            className={styles.input}
          />
        </div>
      </div>

      <div className={styles.toggleGroup}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={buildIntermediates}
            onChange={(e) => onBuildIntermediatesChange(e.target.checked)}
            className={styles.checkbox}
          />
          <span>Build Intermediates (T2/Composite breakdown)</span>
        </label>
      </div>

      <div className={styles.info}>
        <p>Adjusted cost formula:</p>
        <code>
          quantity = base × ((100 - ME) / 100) × (1 - structure) × (1 - rig) × runs
        </code>
      </div>
    </div>
  )
}
