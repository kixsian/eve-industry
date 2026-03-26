import React, { useEffect, useState } from 'react'
import { characterApi, IndustryJob } from '../../api/client'
import styles from './IndustryJobs.module.css'

const ACTIVITY_LABELS: Record<number, string> = {
  1: 'Manufacturing',
  3: 'TE Research',
  4: 'ME Research',
  5: 'Copying',
  8: 'Invention',
  11: 'Reactions',
}

function timeRemaining(endDate: string): string {
  const ms = new Date(endDate).getTime() - Date.now()
  if (ms <= 0) return 'Complete'
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  if (h > 24) return `${Math.floor(h / 24)}d ${h % 24}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export default function IndustryJobs() {
  const [jobs, setJobs] = useState<IndustryJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    characterApi.jobs()
      .then(({ data }) => setJobs(data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load jobs'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className={styles.hint}>Loading jobs...</p>
  if (error) return <p className={styles.error}>{error}</p>
  if (jobs.length === 0) return <p className={styles.hint}>No active industry jobs.</p>

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Activity</th>
            <th>Blueprint</th>
            <th>Runs</th>
            <th>Status</th>
            <th>Time Remaining</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map(job => (
            <tr key={job.job_id}>
              <td className={styles.activity}>{ACTIVITY_LABELS[job.activity_id] ?? `Activity ${job.activity_id}`}</td>
              <td>{job.activity_id === 1 && job.product_name ? job.product_name : job.blueprint_name}</td>
              <td>{job.runs}</td>
              <td>
                <span className={`${styles.status} ${styles[job.status] ?? ''}`}>
                  {job.status}
                </span>
              </td>
              <td className={styles.time}>{timeRemaining(job.end_date)}</td>
              <td className={styles.cost}>{job.cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })} ISK</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
