import WhatsAppSetupForm from "@/components/whatsapp-setup-form"

export default function WhatsAppSetup() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold mb-8">WhatsApp Setup</h1>
      <WhatsAppSetupForm />
    </main>
  )
}

