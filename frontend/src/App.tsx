import React, { useState } from 'react'
import ManufacturingPage from './pages/ManufacturingPage'
import styles from './App.module.css'

function App() {
  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>EVE Manufacturing Calculator</h1>
        <p>Phase 1 MVP - Recursive Material Breakdown</p>
      </header>
      <main className={styles.main}>
        <ManufacturingPage />
      </main>
      <footer className={styles.footer}>
        <p>Manufacturing costs calculated for EVE Online</p>
      </footer>
    </div>
  )
}

export default App
