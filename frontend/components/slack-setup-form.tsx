"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import Link from "next/link"

export default function SlackSetupForm() {
    const [slackToken, setSlackToken] = useState("")
    const [botToken, setBotToken] = useState("")

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        console.log("Slack Token:", slackToken)
        console.log("Bot Token:", botToken)
        // Here you would typically send this data to your backend
        // For this example, we're just logging it to the console
        alert("Slack setup submitted!")
    }

    return (
        <Card className="w-full max-w-md bg-gray-800 text-white">
            <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4 mt-4">
                    <div className="space-y-2">
                        <label htmlFor="slackToken" className="text-sm font-medium">
                            Slack Token
                        </label>
                        <Input
                            id="slackToken"
                            type="text"
                            value={slackToken}
                            onChange={(e) => setSlackToken(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="botToken" className="text-sm font-medium">
                            Bot Token
                        </label>
                        <Input
                            id="botToken"
                            type="text"
                            value={botToken}
                            onChange={(e) => setBotToken(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Link href={`/telegram`}>
                        <Button type="submit" className="w-full">
                            Submit
                        </Button>
                    </Link>
                </CardFooter>
            </form>
        </Card>
    )
}

