"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import Link from "next/link"

export default function GmailSetupForm() {
    const [senderMail, setSenderMail] = useState("")
    const [password, setPassword] = useState("")

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        console.log("Sender Mail:", senderMail)
        console.log("Password:", password)
        // Here you would typically send this data to your backend
        // For this example, we're just logging it to the console
        alert("Gmail setup submitted!")
    }

    return (
        <Card className="w-full max-w-md bg-gray-800 text-white">
            <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4 mt-4">
                    <div className="space-y-2">
                        <label htmlFor="senderMail" className="text-sm font-medium">
                            Sender Mail
                        </label>
                        <Input
                            id="senderMail"
                            type="email"
                            value={senderMail}
                            onChange={(e) => setSenderMail(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="password" className="text-sm font-medium">
                            Password
                        </label>
                        <Input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Link href={`/slack`}>
                        <Button type="submit" className="w-full">
                            Submit
                        </Button>
                    </Link>
                </CardFooter>
            </form>
        </Card>
    )
}

