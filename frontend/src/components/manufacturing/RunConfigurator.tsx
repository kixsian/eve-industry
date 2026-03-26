import React, { useState, useEffect, useRef } from 'react'
import { manufacturingApi } from '../../api/client'
import styles from './RunConfigurator.module.css'

interface SystemResult {
  solarSystemID: number
  solarSystemName: string
  security: number
}

interface RunConfiguratorProps {
  runs: number
  meLevel: number
  structureBonus: number
  rigBonus: number
  buildIntermediates: boolean
  solarSystemId: number | null
  solarSystemName: string
  facilityTaxRate: number
  onRunsChange: (runs: number) => void
  onMeLevelChange: (me: number) => void
  onStructureBonusChange: (bonus: number) => void
  onRigBonusChange: (bonus: number) => void
  onBuildIntermediatesChange: (build: boolean) => void
  onSystemChange: (id: number | null, name: string) => void
  onFacilityTaxRateChange: (rate: number) => void
}

function secColor(sec: number) {
  if (sec >= 0.5) return '#00cc66'
  if (sec >= 0.1) return '#ffcc00'
  return '#ff4444'
}

export const RunConfigurator: React.FC<RunConfiguratorProps> = ({
  runs, meLevel, structureBonus, rigBonus, buildIntermediates,
  solarSystemId, solarSystemName, facilityTaxRate,
  onRunsChange, onMeLevelChange, onStructureBonusChange, onRigBonusChange,
  onBuildIntermediatesChange, onSystemChange, onFacilityTaxRateChange,
}) => {
  const [systemQuery, setSystemQuery] = useState(solarSystemName)
  const [systemResults, setSystemResults] = useState<SystemResult[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSystemSearch = async (q: string) => {
    setSystemQuery(q)
    onSystemChange(null, q)
    if (q.length < 2) { setSystemResults([]); setShowDropdown(false); return }
    try {
      const { data } = await manufacturingApi.searchSystems(q)
      setSystemResults(data.results)
      setShowDropdown(data.results.length > 0)
    } catch {
      setSystemResults([])
    }
  }

  const handleSystemSelect = (system: SystemResult) => {
    setSystemQuery(system.solarSystemName)
    setSystemResults([])
    setShowDropdown(false)
    onSystemChange(system.solarSystemID, system.solarSystemName)
  }

  return (
    <div className={styles.configurator}>
      <div className={styles.configGrid}>
        <div className={styles.configGroup}>
          <label htmlFor="runs">Runs</label>
          <input id="runs" type="number" min="1" max="10000" value={runs}
            onChange={(e) => onRunsChange(Math.max(1, parseInt(e.target.value) || 1))}
            className={styles.input} />
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="meLevel">Material Efficiency (ME)<span className={styles.hint}> 0-10</span></label>
          <div className={styles.meSlider}>
            <input id="meLevel" type="range" min="0" max="10" value={meLevel}
              onChange={(e) => onMeLevelChange(parseInt(e.target.value))}
              className={styles.slider} />
            <span className={styles.meValue}>{meLevel}</span>
          </div>
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="structureBonus">Structure Bonus<span className={styles.hint}> EC=0.01</span></label>
          <input id="structureBonus" type="number" min="0" max="0.1" step="0.001" value={structureBonus}
            onChange={(e) => onStructureBonusChange(parseFloat(e.target.value) || 0)}
            className={styles.input} />
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="rigBonus">Rig Bonus<span className={styles.hint}> T1=0.02</span></label>
          <input id="rigBonus" type="number" min="0" max="0.1" step="0.001" value={rigBonus}
            onChange={(e) => onRigBonusChange(parseFloat(e.target.value) || 0)}
            className={styles.input} />
        </div>

        <div className={styles.configGroup} ref={searchRef}>
          <label>Build System</label>
          <div className={styles.systemSearch}>
            <input
              type="text"
              placeholder="Search system..."
              value={systemQuery}
              onChange={(e) => handleSystemSearch(e.target.value)}
              onFocus={() => systemResults.length > 0 && setShowDropdown(true)}
              className={`${styles.input} ${solarSystemId ? styles.inputSelected : ''}`}
            />
            {showDropdown && (
              <div className={styles.dropdown}>
                {systemResults.map(s => (
                  <div key={s.solarSystemID} className={styles.dropdownItem}
                    onMouseDown={() => handleSystemSelect(s)}>
                    <span className={styles.systemName}>{s.solarSystemName}</span>
                    <span className={styles.secStatus} style={{ color: secColor(s.security) }}>
                      {s.security.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className={styles.configGroup}>
          <label htmlFor="facilityTax">Facility Tax Rate<span className={styles.hint}> e.g. 0.05</span></label>
          <input id="facilityTax" type="number" min="0" max="1" step="0.01" value={facilityTaxRate}
            onChange={(e) => onFacilityTaxRateChange(parseFloat(e.target.value) || 0)}
            className={styles.input} />
        </div>
      </div>

      <div className={styles.toggleGroup}>
        <label className={styles.checkboxLabel}>
          <input type="checkbox" checked={buildIntermediates}
            onChange={(e) => onBuildIntermediatesChange(e.target.checked)}
            className={styles.checkbox} />
          <span>Build Intermediates (T2/Composite breakdown)</span>
        </label>
      </div>
    </div>
  )
}
