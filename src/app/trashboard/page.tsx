"use client";
// import React, { useState, useMemo } from 'react';
// import { Search, Filter, Calendar, Building2, FileText } from 'lucide-react';

// interface Amendment {
//   id: string;
//   title: string;
//   source: string;
//   effectiveDate: string;
//   summary: string;
//   sector: string;
//   tags: string[];
// }

// const hardcodedAmendments: Amendment[] = [
//   {
//     id: '1',
//     title: 'Companies (Amendment) Rules, 2024 - Board Meeting Requirements',
//     source: 'Ministry of Corporate Affairs (MCA)',
//     effectiveDate: '2024-04-01',
//     summary: 'New provisions for mandatory quarterly board meetings and enhanced disclosure requirements for listed companies. Digital attendance provisions updated.',
//     sector: 'Corporate',
//     tags: ['Board Meetings', 'Disclosure', 'Listed Companies']
//   },
//   {
//     id: '2',
//     title: 'SEBI (Mutual Funds) Amendment Regulations, 2024',
//     source: 'Securities and Exchange Board of India (SEBI)',
//     effectiveDate: '2024-03-15',
//     summary: 'Enhanced risk management framework for mutual fund schemes. New guidelines for ESG fund categorization and reporting standards.',
//     sector: 'Finance',
//     tags: ['Mutual Funds', 'ESG', 'Risk Management']
//   },
//   {
//     id: '3',
//     title: 'RBI Master Direction on Digital Payment Security Framework',
//     source: 'Reserve Bank of India (RBI)',
//     effectiveDate: '2024-06-01',
//     summary: 'Strengthened security measures for digital payments including two-factor authentication and fraud monitoring requirements for all payment service providers.',
//     sector: 'Finance',
//     tags: ['Digital Payments', 'Security', 'Authentication']
//   },
//   {
//     id: '4',
//     title: 'Drugs and Cosmetics (Amendment) Rules, 2024',
//     source: 'Central Drugs Standard Control Organisation (CDSCO)',
//     effectiveDate: '2024-05-10',
//     summary: 'Updated quality control standards for pharmaceutical manufacturing. New labeling requirements and mandatory adverse event reporting for drug manufacturers.',
//     sector: 'Healthcare',
//     tags: ['Pharmaceuticals', 'Quality Control', 'Labeling']
//   },
//   {
//     id: '5',
//     title: 'Foreign Trade Policy Amendment - Export Incentive Scheme',
//     source: 'Directorate General of Foreign Trade (DGFT)',
//     effectiveDate: '2024-07-01',
//     summary: 'Enhanced export incentives for textile and electronics sectors. New documentation requirements for claiming benefits under various export promotion schemes.',
//     sector: 'Export',
//     tags: ['Export Incentives', 'Textiles', 'Electronics']
//   },
//   {
//     id: '6',
//     title: 'Environment Clearance Amendment for Manufacturing Units',
//     source: 'Ministry of Environment, Forest and Climate Change',
//     effectiveDate: '2024-08-15',
//     summary: 'Streamlined environmental clearance process for small and medium manufacturing units. New online portal for application submission and tracking.',
//     sector: 'Manufacturing',
//     tags: ['Environmental Clearance', 'SME', 'Online Portal']
//   },
//   {
//     id: '7',
//     title: 'GST Amendment - E-invoicing Threshold Reduction',
//     source: 'Central Board of Indirect Taxes and Customs (CBIC)',
//     effectiveDate: '2024-04-20',
//     summary: 'E-invoicing mandate extended to businesses with turnover above ₹20 crores. New compliance requirements for B2B transactions and input tax credit claims.',
//     sector: 'Tax',
//     tags: ['GST', 'E-invoicing', 'Input Tax Credit']
//   },
//   {
//     id: '8',
//     title: 'Labour Code Implementation - Contract Workers Rights',
//     source: 'Ministry of Labour and Employment',
//     effectiveDate: '2024-09-01',
//     summary: 'Enhanced social security benefits for contract workers. New registration requirements for contractors and mandatory skill development provisions.',
//     sector: 'Labour',
//     tags: ['Contract Workers', 'Social Security', 'Skill Development']
//   },
//   {
//     id: '9',
//     title: 'SEBI (REIT) Amendment Regulations - Investment Limits',
//     source: 'Securities and Exchange Board of India (SEBI)',
//     effectiveDate: '2024-05-25',
//     summary: 'Revised investment limits for Real Estate Investment Trusts. New provisions for foreign investment and minimum public shareholding requirements.',
//     sector: 'Finance',
//     tags: ['REIT', 'Investment Limits', 'Foreign Investment']
//   },
//   {
//     id: '10',
//     title: 'Digital Personal Data Protection Rules Implementation',
//     source: 'Ministry of Electronics and Information Technology',
//     effectiveDate: '2024-10-01',
//     summary: 'Comprehensive data protection framework for digital businesses. New consent management requirements and penalties for data breaches.',
//     sector: 'Technology',
//     tags: ['Data Protection', 'Consent Management', 'Privacy']
//   }
// ];

// const sectors = ['All', 'Corporate', 'Finance', 'Healthcare', 'Export', 'Manufacturing', 'Tax', 'Labour', 'Technology'];

// export default function RegulationFeedDashboard() {
//   const [searchTerm, setSearchTerm] = useState('');
//   const [selectedSector, setSelectedSector] = useState('All');
//   const [dateRange, setDateRange] = useState({ start: '', end: '' });

//   const filteredAmendments = useMemo(() => {
//     return hardcodedAmendments.filter(amendment => {
//       const matchesSearch = searchTerm === '' || 
//         amendment.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
//         amendment.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
//         amendment.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      
//       const matchesSector = selectedSector === 'All' || amendment.sector === selectedSector;
      
//       const matchesDateRange = (!dateRange.start || amendment.effectiveDate >= dateRange.start) &&
//         (!dateRange.end || amendment.effectiveDate <= dateRange.end);
      
//       return matchesSearch && matchesSector && matchesDateRange;
//     });
//   }, [searchTerm, selectedSector, dateRange]);

//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleDateString('en-IN', {
//       year: 'numeric',
//       month: 'short',
//       day: 'numeric'
//     });
//   };

//   return (
//     <div className="min-h-screen bg-black p-6">
//       <div className="max-w-6xl mx-auto">
//         {/* Header */}
//         <div className="text-center mb-8">
//           <h1 className="text-4xl font-bold text-white mb-2">
//             India Regulation Feed
//           </h1>
//           <p className="text-gray-300 text-lg">
//             Stay updated with the latest compliance amendments and regulatory changes
//           </p>
//         </div>

//         {/* Search and Filters */}
//         <div className="bg-gray-900 rounded-2xl shadow-lg p-6 mb-8 border border-emerald-500/20">
//           <div className="flex flex-col lg:flex-row gap-4">
//             {/* Search Bar */}
//             <div className="flex-1 relative">
//               <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
//               <input
//                 type="text"
//                 placeholder="Search amendments, keywords, or tags..."
//                 className="w-full pl-10 pr-4 py-3 bg-black border border-gray-800 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500/50 outline-none text-white placeholder-gray-500"
//                 value={searchTerm}
//                 onChange={(e) => setSearchTerm(e.target.value)}
//               />
//             </div>

//             {/* Sector Filter */}
//             <div className="relative">
//               <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
//               <select
//                 className="pl-10 pr-8 py-3 bg-black border border-gray-800 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500/50 outline-none text-white min-w-40"
//                 value={selectedSector}
//                 onChange={(e) => setSelectedSector(e.target.value)}
//               >
//                 {sectors.map(sector => (
//                   <option key={sector} value={sector}>{sector}</option>
//                 ))}
//               </select>
//             </div>

//             {/* Date Range */}
//             <div className="flex gap-2">
//               <input
//                 type="date"
//                 className="px-3 py-3 bg-black border border-gray-800 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500/50 outline-none text-white"
//                 value={dateRange.start}
//                 onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
//                 placeholder="Start date"
//               />
//               <input
//                 type="date"
//                 className="px-3 py-3 bg-black border border-gray-800 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500/50 outline-none text-white"
//                 value={dateRange.end}
//                 onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
//                 placeholder="End date"
//               />
//             </div>
//           </div>
//         </div>

//         {/* Results Count */}
//         <div className="mb-6">
//           <p className="text-gray-400">
//             Showing {filteredAmendments.length} amendment{filteredAmendments.length !== 1 ? 's' : ''}
//           </p>
//         </div>

//         {/* Amendment Feed */}
//         <div className="space-y-6 max-h-screen overflow-y-auto">
//           {filteredAmendments.map((amendment) => (
//             <div
//               key={amendment.id}
//               className="bg-gradient-to-br from-gray-900 to-black rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 border border-emerald-500/20 hover:border-emerald-500/50"
//             >
//               <div className="p-6">
//                 {/* Header */}
//                 <div className="flex items-start justify-between mb-4">
//                   <div className="flex-1">
//                     <h3 className="text-xl font-semibold text-white mb-2 leading-tight">
//                       {amendment.title}
//                     </h3>
//                     <div className="flex items-center gap-4 text-sm text-gray-300">
//                       <div className="flex items-center gap-1">
//                         <Building2 className="h-4 w-4" />
//                         <span>{amendment.source}</span>
//                       </div>
//                       <div className="flex items-center gap-1">
//                         <Calendar className="h-4 w-4" />
//                         <span>Effective: {formatDate(amendment.effectiveDate)}</span>
//                       </div>
//                     </div>
//                   </div>
//                   <div className="ml-4">
//                     <span className={`px-3 py-1 rounded-full text-xs font-medium ${
//                       amendment.sector === 'Finance' ? 'bg-green-400/10 text-green-400 border border-green-400/20' :
//                       amendment.sector === 'Healthcare' ? 'bg-blue-400/10 text-blue-400 border border-blue-400/20' :
//                       amendment.sector === 'Corporate' ? 'bg-blue-400/10 text-blue-400 border border-blue-400/20' :
//                       amendment.sector === 'Tax' ? 'bg-yellow-400/10 text-yellow-400 border border-yellow-400/20' :
//                       amendment.sector === 'Manufacturing' ? 'bg-red-400/10 text-red-400 border border-red-400/20' :
//                       amendment.sector === 'Export' ? 'bg-green-400/10 text-green-400 border border-green-400/20' :
//                       amendment.sector === 'Labour' ? 'bg-red-400/10 text-red-400 border border-red-400/20' :
//                       'bg-gray-700 text-gray-300 border border-gray-700'
//                     }`}>
//                       {amendment.sector}
//                     </span>
//                   </div>
//                 </div>

//                 {/* Summary */}
//                 <div className="mb-4">
//                   <div className="flex items-start gap-2">
//                     <FileText className="h-4 w-4 text-gray-400 mt-1 flex-shrink-0" />
//                     <p className="text-gray-300 leading-relaxed">{amendment.summary}</p>
//                   </div>
//                 </div>

//                 {/* Tags */}
//                 <div className="flex flex-wrap gap-2">
//                   {amendment.tags.map((tag, index) => (
//                     <span
//                       key={index}
//                       className="px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-medium border border-emerald-500/20"
//                     >
//                       {tag}
//                     </span>
//                   ))}
//                 </div>
//               </div>
//             </div>
//           ))}
//         </div>

//         {filteredAmendments.length === 0 && (
//           <div className="text-center py-12">
//             <div className="bg-gradient-to-br from-gray-900 to-black rounded-2xl shadow-lg p-8 border border-emerald-500/20">
//               <FileText className="h-16 w-16 text-gray-500 mx-auto mb-4" />
//               <h3 className="text-xl font-semibold text-gray-300 mb-2">No amendments found</h3>
//               <p className="text-gray-400">Try adjusting your search criteria or filters</p>
//             </div>
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }
import React, { useState, useMemo } from 'react';
import { Search, Filter, Calendar, Building2, FileText, TestTube, Bell, Settings, ChevronRight } from 'lucide-react';

interface Amendment {
  id: string;
  title: string;
  source: string;
  effectiveDate: string;
  summary: string;
  sector: string;
  tags: string[];
  priority: 'High' | 'Medium' | 'Low';
  complianceScore: number;
}

const hardcodedAmendments: Amendment[] = [
  {
    id: '1',
    title: 'Companies (Amendment) Rules, 2024 - Board Meeting Requirements',
    source: 'Ministry of Corporate Affairs (MCA)',
    effectiveDate: '2024-04-01',
    summary: 'New provisions for mandatory quarterly board meetings and enhanced disclosure requirements for listed companies. Digital attendance provisions updated.',
    sector: 'Corporate',
    tags: ['Board Meetings', 'Disclosure', 'Listed Companies'],
    priority: 'High',
    complianceScore: 95
  },
  {
    id: '2',
    title: 'SEBI (Mutual Funds) Amendment Regulations, 2024',
    source: 'Securities and Exchange Board of India (SEBI)',
    effectiveDate: '2024-03-15',
    summary: 'Enhanced risk management framework for mutual fund schemes. New guidelines for ESG fund categorization and reporting standards.',
    sector: 'Finance',
    tags: ['Mutual Funds', 'ESG', 'Risk Management'],
    priority: 'High',
    complianceScore: 92
  },
  {
    id: '3',
    title: 'RBI Master Direction on Digital Payment Security Framework',
    source: 'Reserve Bank of India (RBI)',
    effectiveDate: '2024-06-01',
    summary: 'Strengthened security measures for digital payments including two-factor authentication and fraud monitoring requirements for all payment service providers.',
    sector: 'Finance',
    tags: ['Digital Payments', 'Security', 'Authentication'],
    priority: 'High',
    complianceScore: 88
  },
  {
    id: '4',
    title: 'Drugs and Cosmetics (Amendment) Rules, 2024',
    source: 'Central Drugs Standard Control Organisation (CDSCO)',
    effectiveDate: '2024-05-10',
    summary: 'Updated quality control standards for pharmaceutical manufacturing. New labeling requirements and mandatory adverse event reporting for drug manufacturers.',
    sector: 'Healthcare',
    tags: ['Pharmaceuticals', 'Quality Control', 'Labeling'],
    priority: 'Medium',
    complianceScore: 85
  },
  {
    id: '5',
    title: 'Foreign Trade Policy Amendment - Export Incentive Scheme',
    source: 'Directorate General of Foreign Trade (DGFT)',
    effectiveDate: '2024-07-01',
    summary: 'Enhanced export incentives for textile and electronics sectors. New documentation requirements for claiming benefits under various export promotion schemes.',
    sector: 'Export',
    tags: ['Export Incentives', 'Textiles', 'Electronics'],
    priority: 'Medium',
    complianceScore: 78
  },
  {
    id: '6',
    title: 'Environment Clearance Amendment for Manufacturing Units',
    source: 'Ministry of Environment, Forest and Climate Change',
    effectiveDate: '2024-08-15',
    summary: 'Streamlined environmental clearance process for small and medium manufacturing units. New online portal for application submission and tracking.',
    sector: 'Manufacturing',
    tags: ['Environmental Clearance', 'SME', 'Online Portal'],
    priority: 'Low',
    complianceScore: 72
  },
  {
    id: '7',
    title: 'GST Amendment - E-invoicing Threshold Reduction',
    source: 'Central Board of Indirect Taxes and Customs (CBIC)',
    effectiveDate: '2024-04-20',
    summary: 'E-invoicing mandate extended to businesses with turnover above ₹20 crores. New compliance requirements for B2B transactions and input tax credit claims.',
    sector: 'Tax',
    tags: ['GST', 'E-invoicing', 'Input Tax Credit'],
    priority: 'High',
    complianceScore: 90
  },
  {
    id: '8',
    title: 'Labour Code Implementation - Contract Workers Rights',
    source: 'Ministry of Labour and Employment',
    effectiveDate: '2024-09-01',
    summary: 'Enhanced social security benefits for contract workers. New registration requirements for contractors and mandatory skill development provisions.',
    sector: 'Labour',
    tags: ['Contract Workers', 'Social Security', 'Skill Development'],
    priority: 'Medium',
    complianceScore: 76
  }
];

const sectors = ['All', 'Corporate', 'Finance', 'Healthcare', 'Export', 'Manufacturing', 'Tax', 'Labour', 'Technology'];

export default function RegulationFeedDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState('All');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const filteredAmendments = useMemo(() => {
    return hardcodedAmendments.filter(amendment => {
      const matchesSearch = searchTerm === '' || 
        amendment.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        amendment.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        amendment.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesSector = selectedSector === 'All' || amendment.sector === selectedSector;
      
      const matchesDateRange = (!dateRange.start || amendment.effectiveDate >= dateRange.start) &&
        (!dateRange.end || amendment.effectiveDate <= dateRange.end);
      
      return matchesSearch && matchesSector && matchesDateRange;
    });
  }, [searchTerm, selectedSector, dateRange]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const recommendedAmendments = hardcodedAmendments
    .filter(a => a.complianceScore >= 85)
    .sort((a, b) => b.complianceScore - a.complianceScore)
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-black">
      <div className="flex">
        {/* Left Sidebar */}
        <div className="w-72 bg-gray-900 border-r border-gray-800">
          <div className="p-6">
            {/* Logo/Brand */}
            <div className="mb-8">
              <h2 className="text-white font-semibold text-xl">Compliance Hub</h2>
              <p className="text-gray-400 text-sm mt-1">Regulatory Intelligence</p>
            </div>

            {/* Test Compliance Button */}
            <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center justify-center gap-2 mb-8">
              <TestTube className="h-4 w-4" />
              Test Compliance
            </button>

            {/* Navigation */}
            <nav className="space-y-2">
              <a href="#" className="flex items-center justify-between px-3 py-2 text-white bg-gray-800 rounded-lg">
                <span className="text-sm font-medium">Regulation Feed</span>
                <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              </a>
              <a href="#" className="flex items-center justify-between px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                <span className="text-sm">Compliance Reports</span>
              </a>
              <a href="#" className="flex items-center justify-between px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                <span className="text-sm">Risk Assessment</span>
              </a>
              <a href="#" className="flex items-center justify-between px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                <span className="text-sm">Team Management</span>
              </a>
            </nav>
          </div>

          {/* Bottom Stats */}
          <div className="absolute bottom-6 left-6 right-6">
            <div className="border-t border-gray-800 pt-4">
              <div className="text-gray-400 text-xs mb-2">Compliance Status</div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white">Overall Score</span>
                <span className="text-emerald-400 font-semibold">84%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Feed Area */}
          <div className="flex-1 p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-2xl font-semibold text-white mb-1">Regulation Feed</h1>
                <p className="text-gray-400">Stay updated with latest compliance changes</p>
              </div>
              <div className="flex items-center gap-3">
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Bell className="h-5 w-5" />
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Settings className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-6">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="text"
                    placeholder="Search amendments..."
                    className="w-full pl-10 pr-4 py-2.5 bg-black border border-gray-700 rounded-lg focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-white placeholder-gray-500"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>

                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <select
                    className="pl-10 pr-8 py-2.5 bg-black border border-gray-700 rounded-lg focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-white min-w-32 appearance-none"
                    value={selectedSector}
                    onChange={(e) => setSelectedSector(e.target.value)}
                  >
                    {sectors.map(sector => (
                      <option key={sector} value={sector} className="bg-black">{sector}</option>
                    ))}
                  </select>
                </div>

                <input
                  type="date"
                  className="px-3 py-2.5 bg-black border border-gray-700 rounded-lg focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-white"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                />
              </div>
            </div>

            {/* Results */}
            <div className="mb-4">
              <p className="text-gray-400 text-sm">{filteredAmendments.length} amendments found</p>
            </div>

            {/* Amendment List */}
            <div className="space-y-4">
              {filteredAmendments.map((amendment) => (
                <div
                  key={amendment.id}
                  className="bg-gray-900 border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-white font-medium text-lg mb-2 leading-tight">
                        {amendment.title}
                      </h3>
                      <div className="flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4" />
                          <span>{amendment.source}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(amendment.effectiveDate)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        amendment.priority === 'High' ? 'bg-red-900/30 text-red-400 border border-red-800' :
                        amendment.priority === 'Medium' ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-800' :
                        'bg-emerald-900/30 text-emerald-400 border border-emerald-800'
                      }`}>
                        {amendment.priority}
                      </span>
                      <span className="text-emerald-400 text-sm font-medium">
                        {amendment.complianceScore}%
                      </span>
                    </div>
                  </div>

                  <p className="text-gray-300 mb-4 leading-relaxed">
                    {amendment.summary}
                  </p>

                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-2">
                      {amendment.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-800 text-gray-300 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      amendment.sector === 'Finance' || amendment.sector === 'Corporate' || amendment.sector === 'Export' 
                        ? 'bg-emerald-900/30 text-emerald-400' 
                        : 'bg-gray-800 text-gray-300'
                    }`}>
                      {amendment.sector}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {filteredAmendments.length === 0 && (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-white font-medium mb-2">No amendments found</h3>
                <p className="text-gray-400">Try adjusting your search criteria</p>
              </div>
            )}
          </div>

          {/* Right Sidebar - Recommendations */}
          <div className="w-80 bg-gray-900 border-l border-gray-800 p-6">
            <h3 className="text-white font-medium text-lg mb-6">Most Relevant</h3>
            
            <div className="space-y-4">
              {recommendedAmendments.map((amendment, index) => (
                <div 
                  key={amendment.id}
                  className="bg-black border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="text-white font-medium text-sm leading-tight">
                      {amendment.title.slice(0, 50)}...
                    </h4>
                    <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  </div>
                  
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400 text-xs">{amendment.source.split(' ')[0]}</span>
                    <span className="text-emerald-400 text-xs font-medium">
                      {amendment.complianceScore}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-1 rounded text-xs ${
                      amendment.sector === 'Finance' || amendment.sector === 'Corporate'
                        ? 'bg-emerald-900/30 text-emerald-400' 
                        : 'bg-gray-800 text-gray-300'
                    }`}>
                      {amendment.sector}
                    </span>
                    <div className="text-xs text-gray-400">
                      #{index + 1}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}