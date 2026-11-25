import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Bot, Sparkles, Building2, Lock, Mail, Phone, User, CheckCircle2, AlertCircle } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [industry, setIndustry] = useState('clinic');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const fillDemoClinic = () => {
    setIsLogin(false);
    setBusinessName('Apex Dental & Orthodontic Clinic');
    setEmail('contact@apexdental.com');
    setPassword('DemoPass123!');
    setFullName('Dr. Ananya Sen');
    setPhone('+919876543210');
    setIndustry('clinic');
  };

  const fillDemoSalon = () => {
    setIsLogin(false);
    setBusinessName('Luxe Velvet Salon & Spa');
    setEmail('reception@luxevelvet.com');
    setPassword('DemoPass123!');
    setFullName('Kabir Malhotra');
    setPhone('+919811223344');
    setIndustry('salon');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login({ email, password });
      } else {
        await register({
          business_name: businessName,
          email,
          password,
          full_name: fullName,
          phone,
          industry,
          timezone
        });
      }
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo and Tagline */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-0.5 shadow-xl shadow-emerald-500/10 mb-4">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-emerald-400">
              <Bot className="w-7 h-7" />
            </div>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">VoiceDesk</h1>
          <p className="text-sm text-slate-400 mt-1">AI-Powered Inbound Voice Receptionist for SaaS</p>
        </div>

        {/* Demo Business One-Click Fill Pills */}
        <div className="mb-4 flex gap-2 justify-center">
          <button
            type="button"
            onClick={fillDemoClinic}
            className="text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 transition-all font-medium flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Quick Demo: Dental Clinic
          </button>
          <button
            type="button"
            onClick={fillDemoSalon}
            className="text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-teal-500/30 text-teal-400 hover:bg-teal-500/10 transition-all font-medium flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Quick Demo: Salon & Spa
          </button>
        </div>

        {/* Main Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
          {/* Tabs */}
          <div className="flex border-b border-slate-800 mb-6">
            <button
              onClick={() => { setIsLogin(true); setError(null); }}
              className={`flex-1 pb-3 text-sm font-semibold transition-colors border-b-2 ${
                isLogin ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(null); }}
              className={`flex-1 pb-3 text-sm font-semibold transition-colors border-b-2 ${
                !isLogin ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Register Business
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Business Name</label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      placeholder="e.g. Apex Health Clinic"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Industry</label>
                    <select
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    >
                      <option value="clinic">Clinic & Health</option>
                      <option value="salon">Salon & Spa</option>
                      <option value="education">Education</option>
                      <option value="real_estate">Real Estate</option>
                      <option value="home_service">Home Services</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Timezone</label>
                    <select
                      value={timezone}
                      onChange={(e) => setTimezone(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    >
                      <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                      <option value="America/New_York">America/New_York (EST)</option>
                      <option value="Europe/London">Europe/London (GMT)</option>
                      <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Owner / Staff Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Dr. Aarav Patel"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Business Phone</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+919876543210"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@business.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : isLogin ? (
                'Sign In to Receptionist Dashboard'
              ) : (
                'Create Business & Initialize AI Agent'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
