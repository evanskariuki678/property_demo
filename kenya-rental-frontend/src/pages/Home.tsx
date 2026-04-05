import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Building2, Shield, CreditCard, Wrench, BarChart3, Users, ChevronRight } from 'lucide-react';

const features = [
  { icon: Building2, title: 'Property Management', desc: 'Manage multiple properties, units, and track occupancy in one place.' },
  { icon: Users, title: 'Tenant Portal', desc: 'Tenants can view leases, make payments, and submit maintenance requests.' },
  { icon: CreditCard, title: 'M-Pesa Payments', desc: 'Integrated Lipa Na M-Pesa for seamless rent collection via STK Push.' },
  { icon: Wrench, title: 'Maintenance Tracking', desc: 'Track and manage maintenance requests from submission to resolution.' },
  { icon: BarChart3, title: 'Financial Reports', desc: 'Comprehensive revenue, expense, and occupancy analytics.' },
  { icon: Shield, title: 'Kenya DPA Compliant', desc: 'Built with Kenya Data Protection Act 2019 compliance in mind.' },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b bg-white/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="h-7 w-7 text-green-700" />
            <span className="font-bold text-lg text-green-800">KenyaRentals</span>
          </div>
          <div className="flex gap-2">
            <Link to="/login"><Button variant="ghost">Sign In</Button></Link>
            <Link to="/register"><Button>Get Started</Button></Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="py-20 px-4 bg-gradient-to-br from-green-50 via-white to-green-50">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Modern Property Management
            <span className="text-green-700"> for Kenya</span>
          </h1>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Streamline rent collection with M-Pesa, manage tenants, track maintenance requests, and generate financial reports — all in one platform built for Kenyan landlords and property managers.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/register">
              <Button size="lg" className="gap-2">
                Start Free <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline">View Demo</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">Everything You Need</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.title} className="bg-white p-6 rounded-xl shadow-sm border hover:shadow-md transition-shadow">
                  <div className="h-10 w-10 rounded-lg bg-green-50 flex items-center justify-center mb-4">
                    <Icon className="h-5 w-5 text-green-700" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                  <p className="text-sm text-gray-600">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to Simplify Your Property Management?</h2>
          <p className="text-gray-600 mb-8">Join landlords across Kenya who are using KenyaRentals to manage their properties efficiently.</p>
          <Link to="/register">
            <Button size="lg">Create Your Account</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-green-700" />
            <span className="font-semibold text-green-800">KenyaRentals</span>
          </div>
          <p className="text-sm text-gray-500">&copy; {new Date().getFullYear()} KenyaRentals. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
