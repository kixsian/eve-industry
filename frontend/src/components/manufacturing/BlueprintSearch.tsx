import React, { useState, useCallback } from 'react'
import { manufacturingApi } from '../../api/client'
import styles from './BlueprintSearch.module.css'

interface SearchResult {
  typeID: number
  typeName: string
  groupID: number
}

interface BlueprintSearchProps {
  onSelect: (typeId: number, typeName: string) => void
}

export const BlueprintSearch: React.FC<BlueprintSearchProps> = ({ onSelect }) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)

  const handleSearch = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)

    if (value.length < 2) {
      setResults([])
      setShowResults(false)
      return
    }

    setLoading(true)
    try {
      const response = await manufacturingApi.search(value, 20)
      setResults(response.data.results || [])
      setShowResults(true)
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSelect = (typeId: number, typeName: string) => {
    onSelect(typeId, typeName)
    setQuery('')
    setResults([])
    setShowResults(false)
  }

  return (
    <div className={styles.searchContainer}>
      <input
        type="text"
        className={styles.input}
        placeholder="Search for a blueprint or item..."
        value={query}
        onChange={handleSearch}
        onFocus={() => query.length >= 2 && setShowResults(true)}
      />
      {loading && <div className={styles.loading}>Searching...</div>}
      {showResults && results.length > 0 && (
        <div className={styles.resultsList}>
          {results.map((result) => (
            <button
              key={result.typeID}
              className={styles.resultItem}
              onClick={() => handleSelect(result.typeID, result.typeName)}
            >
              <span className={styles.resultName}>{result.typeName}</span>
              <span className={styles.resultId}>ID: {result.typeID}</span>
            </button>
          ))}
        </div>
      )}
      {showResults && results.length === 0 && query.length >= 2 && !loading && (
        <div className={styles.noResults}>No results found</div>
      )}
    </div>
  )
}
