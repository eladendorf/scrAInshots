"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Activity, Settings as SettingsIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Navigation() {
  const pathname = usePathname()

  const isActive = (path: string) => pathname === path

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <h1 className="text-xl font-bold">ScrAInshots</h1>
            
            <div className="flex space-x-4">
              <Link href="/">
                <Button
                  variant={isActive('/') ? 'default' : 'ghost'}
                  size="sm"
                  className="flex items-center space-x-2"
                >
                  <Home className="h-4 w-4" />
                  <span>Gallery</span>
                </Button>
              </Link>
              
              <Link href="/processing">
                <Button
                  variant={isActive('/processing') ? 'default' : 'ghost'}
                  size="sm"
                  className="flex items-center space-x-2"
                >
                  <Activity className="h-4 w-4" />
                  <span>Processing</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}