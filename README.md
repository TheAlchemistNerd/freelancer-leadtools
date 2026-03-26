# Freelancer LeadTools

**Free Marketing Calculators for Lead Generation**

A collection of free, SEO-optimized calculators that help freelancers and agencies make better decisions while capturing leads for our paid products.

## 🎯 Purpose

- **Attract** potential users through valuable free tools
- **Educate** users about their freelance business health
- **Convert** users to paid products (freelance-growth, freelancer-dealflow)

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run locally
python app/main.py

# Or with Next.js frontend
npm run dev
```

## 📊 Calculator Categories

### For Individual Freelancers → freelance-growth

| Calculator | Description | CTA |
|------------|-------------|-----|
| Burnout Risk Calculator | Assess burnout risk based on work habits | "Get personalized coaching" |
| Skill Gap Scanner | Identify skills needed for target role | "Create learning plan" |
| Portfolio Score | Evaluate portfolio strength | "Get improvement plan" |
| Client Fit Score | Evaluate if a client is worth working with | "Track client relationships" |
| Scope Creep Calculator | Calculate cost of additional requests | "Set boundaries with templates" |
| Hourly Rate Calculator | Determine optimal hourly rate | "Track time effectively" |
| Freelance vs Full-time ROI | Compare earnings potential | "Manage freelance finances" |

### For Agencies → freelancer-dealflow

| Calculator | Description | CTA |
|------------|-------------|-----|
| Agency Profit Margin | Calculate actual profit after expenses | "Track agency finances" |
| Team Utilization Rate | Measure team productivity | "Optimize team capacity" |
| Client LTV Calculator | Calculate client lifetime value | "Manage client relationships" |
| Proposal Win Rate | Analyze proposal success | "Improve proposals with AI" |
| Cash Flow Forecast | Predict future cash position | "Manage agency finances" |
| Break-even Analysis | Determine minimum revenue needed | "Track agency metrics" |

### For Both → Either Product

| Calculator | Description | CTA |
|------------|-------------|-----|
| Rate Calculator (PPP) | Location-adjusted rate calculator | "Get accurate time tracking" |
| Tax Estimator | Estimate quarterly taxes | "Track business expenses" |
| Retirement Planner | Plan for retirement as freelancer | "Plan long-term finances" |
| Time Value Calculator | Calculate opportunity cost | "Optimize time allocation" |

## 🏗️ Architecture

```
freelancer-leadtools/
├── app/                    # FastAPI backend
│   ├── main.py
│   ├── routes/
│   │   ├── individuals.py  # Individual calculators
│   │   ├── agencies.py     # Agency calculators
│   │   └── shared.py       # Shared calculators
│   ├── schemas/            # Pydantic models
│   ├── services/           # Business logic
│   └── templates/          # Email templates
├── pages/                  # Next.js frontend (SEO)
│   ├── calculators/
│   └── blog/
├── tests/
├── requirements.txt
├── package.json
└── vercel.json
```

## 📈 Lead Capture Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Free Calculator                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Input: Weekly hours, sleep, context switches          │  │
│  │ [Calculate My Burnout Risk]                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Result: Your Burnout Risk Score: 72/100 (HIGH)        │  │
│  │                                                        │  │
│  │ ✓ Basic interpretation (FREE)                         │  │
│  │ ✓ 3 immediate tips (FREE)                             │  │
│  │                                                        │  │
│  │ ───────────────────────────────────────────────────── │  │
│  │                                                        │  │
│  │ 📧 Email me my full 7-day recovery plan               │  │
│  │ [Enter email] [Send My Plan] ← LEAD CAPTURE           │  │
│  │                                                        │  │
│  │ ───────────────────────────────────────────────────── │  │
│  │                                                        │  │
│  │ 🚀 Want ongoing tracking & coaching?                  │  │
│  │ [Start Free Trial →] → freelance-growth               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Frontend | Next.js 14 (App Router) |
| Styling | Tailwind CSS + Shadcn UI |
| Analytics | Plausible (privacy-focused) |
| Email | ConvertKit API |
| Deployment | Vercel (Edge CDN) |
| Monitoring | Vercel Analytics |

## 📊 SEO Strategy

Each calculator targets specific keywords:

| Calculator | Target Keywords |
|------------|-----------------|
| Burnout Calculator | "freelance burnout test", "burnout risk calculator" |
| Rate Calculator | "freelance hourly rate calculator", "what should I charge" |
| Portfolio Score | "portfolio review for freelancers", "portfolio strength" |
| Agency Profit | "agency profit margin calculator", "creative agency profits" |

## 🎨 Design Principles

1. **Fast** - Page load < 2 seconds
2. **Mobile-first** - 60%+ traffic is mobile
3. **Accessible** - WCAG 2.1 AA compliant
4. **Shareable** - Easy to share results on social media

## 📝 License

MIT License - see LICENSE file

---

**Part of the Freelancer Ecosystem**
- [freelancer-core](https://github.com/your-org/freelancer-core) - Shared library
- [freelance-growth](https://github.com/your-org/freelance-growth) - Individual freelancer SaaS
- [freelancer-dealflow](https://github.com/your-org/freelancer-dealflow) - Agency management SaaS
