import TelegramSetupForm from "@/components/telegram-setup-form"

export default function TelegramSetup() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold mb-8">Telegram Setup</h1>
      <TelegramSetupForm />
    </main>
  )
}

