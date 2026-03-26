import React from 'react'
import { authApi, AuthStatus } from '../../api/client'
import styles from './CharacterPanel.module.css'

interface Props {
  status: AuthStatus
  wallet: number | null
  onLogout: () => void
}

function formatISK(value: number): string {
  if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(2) + 'b ISK'
  if (value >= 1_000_000) return (value / 1_000_000).toFixed(2) + 'm ISK'
  if (value >= 1_000) return (value / 1_000).toFixed(1) + 'k ISK'
  return value.toFixed(2) + ' ISK'
}

export default function CharacterPanel({ status, wallet, onLogout }: Props) {
  if (!status.authenticated) {
    return (
      <a href={authApi.loginUrl} className={styles.loginBtn}>
        Login with EVE
      </a>
    )
  }

  return (
    <div className={styles.panel}>
      <img src={status.portrait} alt={status.character_name} className={styles.portrait} />
      <div className={styles.info}>
        <span className={styles.name}>{status.character_name}</span>
        {wallet !== null && (
          <span className={styles.wallet}>{formatISK(wallet)}</span>
        )}
      </div>
      <button className={styles.logoutBtn} onClick={onLogout}>Logout</button>
    </div>
  )
}
