import GmailSetupForm from "@/components/gmail-setup-form"

export default function GmailSetup() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold mb-8">Gmail Setup</h1>
      <GmailSetupForm />
    </main>
  )
}

