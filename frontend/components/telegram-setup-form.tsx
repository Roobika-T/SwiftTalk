"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import Link from "next/link"

export default function TelegramSetupForm() {
    const [apiId, setApiId] = useState("")
    const [apiHash, setApiHash] = useState("")

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        console.log("API ID:", apiId)
        console.log("API Hash:", apiHash)
        // Here you would typically send this data to your backend
        // For this example, we're just logging it to the console
        alert("Telegram setup submitted!")
    }

    return (
        <Card className="w-full max-w-md bg-gray-800 text-white">
            <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4 mt-4">
                    <div className="space-y-2">
                        <label htmlFor="apiId" className="text-sm font-medium">
                            API ID
                        </label>
                        <Input
                            id="apiId"
                            type="text"
                            value={apiId}
                            onChange={(e) => setApiId(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="apiHash" className="text-sm font-medium">
                            API Hash
                        </label>
                        <Input
                            id="apiHash"
                            type="text"
                            value={apiHash}
                            onChange={(e) => setApiHash(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Link href={`/whatsapp`}>
                        <Button type="submit" className="w-full">
                            Submit
                        </Button>
                    </Link>
                </CardFooter>
            </form>
        </Card>
    )
}