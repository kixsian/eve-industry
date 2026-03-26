import React from 'react'
import ManufacturingPage from './pages/ManufacturingPage'
import CharacterPanel from './components/character/CharacterPanel'
import IndustryJobs from './components/character/IndustryJobs'
import { useAuth } from './hooks/useAuth'
import styles from './App.module.css'

function App() {
  const { status, wallet, loading, logout } = useAuth()

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1>EVE Manufacturing Calculator</h1>
        </div>
        <div className={styles.headerRight}>
          {!loading && (
            <CharacterPanel status={status} wallet={wallet} onLogout={logout} />
          )}
        </div>
      </header>

      <main className={styles.main}>
        <ManufacturingPage />

        {status.authenticated && (
          <section className={styles.jobsSection}>
            <h2 className={styles.sectionTitle}>Active Industry Jobs</h2>
            <IndustryJobs />
          </section>
        )}
      </main>

      <footer className={styles.footer}>
        <p>Manufacturing costs calculated for EVE Online</p>
      </footer>
    </div>
  )
}

export default App
