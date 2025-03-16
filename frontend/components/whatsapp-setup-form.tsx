"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import Link from "next/link"

export default function WhatsAppSetupForm() {
    const [phoneNumber, setPhoneNumber] = useState("")

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        console.log("Phone Number:", phoneNumber)
        // Here you would typically send this data to your backend
        // For this example, we're just logging it to the console
        alert("WhatsApp setup submitted!")
    }

    return (
        <Card className="w-full max-w-md bg-gray-800 text-white">
            <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4 mt-4">
                    <div className="space-y-2">
                        <label htmlFor="phoneNumber" className="text-sm font-medium">
                            Phone Number
                        </label>
                        <Input
                            id="phoneNumber"
                            type="tel"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            required
                            className="bg-gray-700 border-gray-600"
                            placeholder="e.g., +1234567890"
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Link href={`/dashboard`}>
                        <Button type="submit" className="w-full">
                            Submit
                        </Button>
                    </Link>
                </CardFooter>
            </form>
        </Card>
    )
}   