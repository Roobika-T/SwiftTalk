"use client"

import type React from "react"
import { useState, useEffect, useCallback } from "react"
import { Slack, Send, MessageCircle, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { toast, ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"

type Service = "slack" | "telegram" | "whatsapp" | "gmail"
const baseURL = "http://localhost:5000"

interface Message {
  [key: string]: any
}

export default function MonitoringDashboard() {
  const [runningServices, setRunningServices] = useState<Set<Service>>(new Set())
  const [messages, setMessages] = useState<Record<Service, Message>>({
    slack: {},
    telegram: {},
    whatsapp: {},
    gmail: {},
  })

  const toggleService = async (service: Service) => {
    const isRunning = runningServices.has(service)
    const action = isRunning ? "stop" : "start"
    const endpoint = `${baseURL}/${action}_${service}`

    try {
      const response = await fetch(endpoint, { method: "POST" })
      const data = await response.json()

      if (response.ok) {
        setRunningServices((prev) => {
          const newSet = new Set(prev)
          isRunning ? newSet.delete(service) : newSet.add(service)
          return newSet
        })
        toast.success(data.message)
      } else {
        toast.error(data.message)
      }
    } catch (error) {
      toast.error(`Failed to ${action} ${service} monitoring`)
    }
  }

  const fetchMessages = useCallback(async (service: Service) => {
    try {
      const response = await fetch(`${baseURL}/${service}.json`)
      const data = await response.json()
      if (response.ok) {
        setMessages((prev) => ({ ...prev, [service]: data }))
      }
    } catch (error) {
      console.error(`Failed to fetch ${service} messages:`, error)
    }
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      runningServices.forEach((service) => fetchMessages(service))
    }, 5000) // Fetch every 5 seconds

    return () => clearInterval(interval)
  }, [runningServices, fetchMessages])

  const services: { name: Service; icon: React.ReactNode; description: string }[] = [
    { name: "slack", icon: <Slack className="h-6 w-6" />, description: "Monitor Slack messages" },
    { name: "telegram", icon: <Send className="h-6 w-6" />, description: "Track Telegram activity" },
    { name: "whatsapp", icon: <MessageCircle className="h-6 w-6" />, description: "Watch WhatsApp conversations" },
    { name: "gmail", icon: <Mail className="h-6 w-6" />, description: "Observe Gmail inbox" },
  ]

  const renderMessages = (service: Service) => {
    const serviceData = messages[service]
    let serviceMessages: any[] = []

    // Extract messages based on service-specific structure
    if (service === "slack") {
      serviceMessages = serviceData.messages || []
    } else if (service === "telegram") {
      serviceMessages = serviceData.messages || []
    } else if (service === "whatsapp") {
      serviceMessages = (serviceData.conversations || []).flatMap((conv: any) => conv.messages || [])
    } else if (service === "gmail") {
      serviceMessages = (serviceData.emails || []).map((email: any) => email.message || {})
    }

    if (!serviceMessages.length) {
      return <p className="text-muted-foreground text-center">No messages to display.</p>
    }

    return (
      <ScrollArea className="h-[250px]">
        {serviceMessages.map((msg, index) => (
          <div key={index} className="mb-3 p-3 bg-secondary rounded-md shadow-sm">
            {service === "slack" && (
              <>
                <div className="flex justify-between items-center">
                  <p className="font-semibold text-primary">{msg.sender || "Unknown"}</p>
                  <Badge variant={msg.priority === "Urgent" ? "destructive" : msg.priority === "Follow-up" ? "secondary" : "outline"}>
                    {msg.priority || "Low Priority"}
                  </Badge>
                </div>
                <p className="mt-1">{msg.message || "No content"}</p>
                <p className="text-sm text-muted-foreground mt-1">{msg.timestamp || "No timestamp"}</p>
                <p className="text-sm italic text-muted-foreground">Response: {msg.suggested_response || "N/A"}</p>
              </>
            )}
            {service === "telegram" && (
              <>
                <div className="flex justify-between items-center">
                  <p className="font-semibold text-primary">{msg.sender || "Unknown"}</p>
                  <Badge variant={msg.priority === "Urgent" ? "destructive" : msg.priority === "Follow-up" ? "secondary" : "outline"}>
                    {msg.priority || "Low Priority"}
                  </Badge>
                </div>
                <p className="mt-1">{msg.message || "No content"}</p>
                <p className="text-sm text-muted-foreground mt-1">{msg.timestamp || "No timestamp"}</p>
                <p className="text-sm italic text-muted-foreground">Response: {msg.suggested_response || "N/A"}</p>
              </>
            )}
            {service === "whatsapp" && (
              <>
                <div className="flex justify-between items-center">
                  <p className="font-semibold text-primary">{msg.contact_name || "Unknown"}</p>
                  <Badge variant={msg.priority === "Urgent" ? "destructive" : msg.priority === "Follow-up" ? "secondary" : "outline"}>
                    {msg.priority || "Low Priority"}
                  </Badge>
                </div>
                <p className="mt-1">{msg.message || "No content"}</p>
                <p className="text-sm text-muted-foreground mt-1">{msg.timestamp || "No timestamp"}</p>
                <p className="text-sm italic text-muted-foreground">Response: {msg.response_sent || msg.suggested_response || "N/A"}</p>
              </>
            )}
            {service === "gmail" && (
              <>
                <div className="flex justify-between items-center">
                  <p className="font-semibold text-primary">{msg.sender || "Unknown"}</p>
                  <Badge variant={msg.priority === "Urgent" ? "destructive" : msg.priority === "Follow-up" ? "secondary" : "outline"}>
                    {msg.priority || "Low Priority"}
                  </Badge>
                </div>
                <p className="font-medium mt-1">{msg.subject || "No Subject"}</p>
                <p className="mt-1">{msg.body || "No content"}</p>
                <p className="text-sm text-muted-foreground mt-1">{msg.timestamp || "No timestamp"}</p>
                <p className="text-sm italic text-muted-foreground">Response: {msg.response_sent || "N/A"}</p>
              </>
            )}
          </div>
        ))}
      </ScrollArea>
    )
  }

  return (
    <div className="container mx-auto p-6 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-8 text-center text-gray-800">Monitoring Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {services.map(({ name, icon, description }) => (
          <Card key={name} className="border-gray-200 shadow-lg hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-gray-100 to-gray-200">
              <CardTitle className="flex items-center space-x-2 text-gray-800">
                {icon}
                <span className="capitalize">{name}</span>
              </CardTitle>
              <CardDescription className="text-gray-600">{description}</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <Button
                onClick={() => toggleService(name)}
                variant={runningServices.has(name) ? "destructive" : "default"}
                className={`w-full mb-4 ${runningServices.has(name) ? "hover:bg-red-700" : "hover:bg-blue-600"}`}
              >
                {runningServices.has(name) ? "Stop" : "Start"} Monitoring
              </Button>
              {renderMessages(name)}
            </CardContent>
          </Card>
        ))}
      </div>
      <ToastContainer position="bottom-right" theme="dark" />
    </div>
  )
}