import MonitoringDashboard from "@/components/monitoring-dashboard"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="container mx-auto py-8">
        <h1 className="text-4xl font-bold text-center mb-8">Monitoring Dashboard</h1>
        <MonitoringDashboard />
      </div>
    </main>
  )
}