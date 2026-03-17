import React, { useState } from 'react'
import { BlueprintSearch } from '../components/manufacturing/BlueprintSearch'
import { RunConfigurator } from '../components/manufacturing/RunConfigurator'
import { MaterialTree } from '../components/manufacturing/MaterialTree'
import { CostSummary } from '../components/manufacturing/CostSummary'
import { manufacturingApi, ManufacturingResponse } from '../api/client'
import styles from './ManufacturingPage.module.css'

export default function ManufacturingPage() {
  const [selectedProduct, setSelectedProduct] = useState<{
    id: number
    name: string
  } | null>(null)
  const [runs, setRuns] = useState(1)
  const [meLevel, setMeLevel] = useState(0)
  const [structureBonus, setStructureBonus] = useState(0.01)
  const [rigBonus, setRigBonus] = useState(0.02)
  const [buildIntermediates, setBuildIntermediates] = useState(true)
  const [result, setResult] = useState<ManufacturingResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSelectProduct = (typeId: number, typeName: string) => {
    setSelectedProduct({ id: typeId, name: typeName })
    setError(null)
  }

  const handleCalculate = async () => {
    if (!selectedProduct) {
      setError('Please select a product')
      return
    }

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
          <BlueprintSearch onSelect={handleSelectProduct} />

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
            runs={runs}
            meLevel={meLevel}
            structureBonus={structureBonus}
            rigBonus={rigBonus}
            buildIntermediates={buildIntermediates}
            onRunsChange={setRuns}
            onMeLevelChange={setMeLevel}
            onStructureBonusChange={setStructureBonus}
            onRigBonusChange={setRigBonus}
            onBuildIntermediatesChange={setBuildIntermediates}
          />

          <button
            className={styles.calculateButton}
            onClick={handleCalculate}
            disabled={!selectedProduct || loading}
          >
            {loading ? 'Calculating...' : 'Calculate Costs'}
          </button>

          {error && <div className={styles.error}>{error}</div>}
        </section>

        {result && (
          <>
            <section className={styles.section}>
              <CostSummary
                summary={result.cost_summary}
                productName={result.product.typeName}
              />
            </section>

            <section className={styles.section}>
              <MaterialTree tree={result.material_tree} />
            </section>

            <section className={styles.section}>
              <h3>Shopping List (Flat Materials)</h3>
              <div className={styles.flatMaterialsList}>
                {result.flat_materials.length === 0 ? (
                  <p>No materials needed</p>
                ) : (
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Material</th>
                        <th>Needed</th>
                        <th>Owned</th>
                        <th>To Buy</th>
                        <th>Unit Price</th>
                        <th>Total Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.flat_materials.map((material) => (
                        <tr key={material.type_id}>
                          <td>{material.type_name}</td>
                          <td className={styles.number}>
                            {material.quantity_needed.toFixed(0)}
                          </td>
                          <td className={styles.number}>{material.quantity_owned.toFixed(0)}</td>
                          <td className={styles.number}>
                            {material.quantity_to_buy.toFixed(0)}
                          </td>
                          <td className={styles.number}>
                            {material.unit_price.toLocaleString()}
                          </td>
                          <td className={styles.number}>
                            {material.total_cost.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}
