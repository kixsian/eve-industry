import React, { useState } from 'react'
import { BlueprintSearch } from '../components/manufacturing/BlueprintSearch'
import { RunConfigurator } from '../components/manufacturing/RunConfigurator'
import { MaterialTree } from '../components/manufacturing/MaterialTree'
import { CostSummary } from '../components/manufacturing/CostSummary'
import { manufacturingApi, ManufacturingResponse, MaterialNode } from '../api/client'
import styles from './ManufacturingPage.module.css'

function formatISK(v: number) {
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

function formatQty(v: number) {
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

interface MaterialTableProps {
  materials: MaterialNode[]
  title: string
  subtitle: string
  totalCost: number
}

function MaterialTable({ materials, title, subtitle, totalCost }: MaterialTableProps) {
  const totalOwned = materials.reduce((s, m) => s + m.quantity_owned, 0)
  const hasOwned = totalOwned > 0

  return (
    <div className={styles.materialFrame}>
      <div className={styles.frameHeader}>
        <h3 className={styles.frameTitle}>{title}</h3>
        <span className={styles.frameSubtitle}>{subtitle}</span>
      </div>
      <div className={styles.frameBody}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Material</th>
              <th className={styles.number}>Needed</th>
              {hasOwned && <th className={styles.number}>In Stock</th>}
              <th className={styles.number}>To Buy</th>
              <th className={styles.number}>Unit Price</th>
              <th className={styles.number}>Cost</th>
            </tr>
          </thead>
          <tbody>
            {materials.map((m) => {
              const isOwned = m.quantity_owned > 0
              const fullyOwned = m.quantity_to_buy === 0
              return (
                <tr key={m.type_id} className={isOwned ? styles.owned : ''}>
                  <td>{m.type_name}</td>
                  <td className={styles.number}>{formatQty(m.quantity_needed)}</td>
                  {hasOwned && (
                    <td className={styles.ownedQty}>
                      {m.quantity_owned > 0 ? formatQty(m.quantity_owned) : '—'}
                    </td>
                  )}
                  <td className={styles.buyQty}>{formatQty(m.quantity_to_buy)}</td>
                  <td className={styles.number}>{formatISK(m.unit_price)}</td>
                  <td className={styles.costCell}>
                    {formatISK(m.total_cost)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className={styles.frameFooter}>
        <span className={styles.footerLabel}>Total to buy</span>
        <span className={styles.footerCost}>{formatISK(totalCost)} ISK</span>
      </div>
    </div>
  )
}

export default function ManufacturingPage() {
  const [selectedProduct, setSelectedProduct] = useState<{ id: number; name: string } | null>(null)
  const [runs, setRuns] = useState(1)
  const [meLevel, setMeLevel] = useState(0)
  const [structureBonus, setStructureBonus] = useState(0.01)
  const [rigBonus, setRigBonus] = useState(0.02)
  const [buildIntermediates, setBuildIntermediates] = useState(true)
  const [solarSystemId, setSolarSystemId] = useState<number | null>(null)
  const [solarSystemName, setSolarSystemName] = useState('')
  const [facilityTaxRate, setFacilityTaxRate] = useState(0.0)
  const [result, setResult] = useState<ManufacturingResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCalculate = async () => {
    if (!selectedProduct) { setError('Please select a product'); return }
    setLoading(true)
    setError(null)
    try {
      const response = await manufacturingApi.calculate({
        product_type_id: selectedProduct.id,
        runs,
        me_level: meLevel,
        structure_bonus: structureBonus,
        rig_bonus: rigBonus,
        build_intermediates: buildIntermediates,
        solar_system_id: solarSystemId ?? undefined,
        facility_tax_rate: facilityTaxRate,
      })
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Calculation failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <section className={styles.section}>
          <h2>Product Selection</h2>
          <BlueprintSearch onSelect={(id, name) => { setSelectedProduct({ id, name }); setError(null) }} />
          {selectedProduct && (
            <div className={styles.selectedProduct}>
              <span className={styles.selected}>
                Selected: <strong>{selectedProduct.name}</strong> (ID: {selectedProduct.id})
              </span>
            </div>
          )}
        </section>

        <section className={styles.section}>
          <h2>Manufacturing Configuration</h2>
          <RunConfigurator
            runs={runs} meLevel={meLevel} structureBonus={structureBonus}
            rigBonus={rigBonus} buildIntermediates={buildIntermediates}
            solarSystemId={solarSystemId} solarSystemName={solarSystemName}
            facilityTaxRate={facilityTaxRate}
            onRunsChange={setRuns} onMeLevelChange={setMeLevel}
            onStructureBonusChange={setStructureBonus} onRigBonusChange={setRigBonus}
            onBuildIntermediatesChange={setBuildIntermediates}
            onSystemChange={(id, name) => { setSolarSystemId(id); setSolarSystemName(name) }}
            onFacilityTaxRateChange={setFacilityTaxRate}
          />
          <button className={styles.calculateButton} onClick={handleCalculate} disabled={!selectedProduct || loading}>
            {loading ? 'Calculating...' : 'Calculate Costs'}
          </button>
          {error && <div className={styles.error}>{error}</div>}
        </section>

        {result && (
          <>
            <section className={styles.section}>
              <CostSummary summary={result.cost_summary} productName={result.product.typeName} />
            </section>

            <section className={styles.section}>
              <MaterialTree tree={result.material_tree} />
            </section>

            <section className={styles.section}>
              <div className={styles.materialsGrid}>
                <MaterialTable
                  materials={result.flat_materials}
                  title="Raw Materials"
                  subtitle="Buy minerals & moon goo"
                  totalCost={result.cost_summary.material_cost}
                />
                <MaterialTable
                  materials={result.direct_components}
                  title="Buy Components"
                  subtitle="Buy intermediate components off market"
                  totalCost={result.cost_summary.component_buy_cost}
                />
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}
