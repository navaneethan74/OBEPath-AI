import React, { useState } from 'react';
import {
  BookOpen,
  FileText,
  Download,
  ExternalLink,
  Search,
  Code2,
  BookMarked,
  Sparkles,
  Layers,
  ChevronRight,
  Filter
} from 'lucide-react';
import { useStudentLearning } from '../context/StudentLearningContext';

interface ResourceItem {
  id: string;
  title: string;
  category: 'Cheat Sheets' | 'Lecture Notes' | 'Code Repositories' | 'Practice Sets';
  description: string;
  format: string;
  sizeOrTime: string;
  courseCode: string;
  downloadUrl?: string;
  badgeColor: string;
}

export const ResourcesPage: React.FC = () => {
  const { studentState, activeCourse } = useStudentLearning();
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';

  // Curated educational resources by course code
  const allCourseResources: Record<string, ResourceItem[]> = {
    CS201: [
      {
        id: 'cs201-1',
        title: 'Big-O Algorithm Complexity & Data Structures Cheat Sheet',
        category: 'Cheat Sheets',
        description: 'Comprehensive quick-reference table for time and space complexity of arrays, stacks, queues, trees, and hash tables.',
        format: 'PDF Guide',
        sizeOrTime: '2.4 MB • 4 pages',
        courseCode: 'CS201',
        badgeColor: 'bg-orange-50 text-orange-700 border-orange-200'
      },
      {
        id: 'cs201-2',
        title: 'Stack & Queue Implementation in Python & C++',
        category: 'Code Repositories',
        description: 'Clean, verified implementations of stack push/pop, queue enqueue/dequeue, circular queues, and deque with unit tests.',
        format: 'Interactive Code',
        sizeOrTime: '15 Code Modules',
        courseCode: 'CS201',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200'
      },
      {
        id: 'cs201-3',
        title: 'Recursion Tracing & Call Stack Visual Workbook',
        category: 'Lecture Notes',
        description: 'Step-by-step visual breakdowns of base cases, recursive branches, Fibonacci call trees, and Hanoi tower state diagrams.',
        format: 'Annotated Slides',
        sizeOrTime: '3.8 MB • 28 slides',
        courseCode: 'CS201',
        badgeColor: 'bg-cream-100 text-amber-800 border-amber-200'
      },
      {
        id: 'cs201-4',
        title: 'Binary Search Trees & Traversal Problem Set',
        category: 'Practice Sets',
        description: '25 curated problem scenarios covering in-order, pre-order, post-order, insertion, deletion, and height balancing with solutions.',
        format: 'Exercises + Sol',
        sizeOrTime: '25 Problems',
        courseCode: 'CS201',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200'
      },
      {
        id: 'cs201-5',
        title: 'Standard Course Outcomes (CO1-CO4) Study Syllabus',
        category: 'Lecture Notes',
        description: 'Official Outcome-Based Education competency goals, bloom taxonomy levels, and prerequisite mapping for CS201.',
        format: 'Syllabus Doc',
        sizeOrTime: '1.2 MB • 6 pages',
        courseCode: 'CS201',
        badgeColor: 'bg-slate-100 text-slate-700 border-slate-200'
      }
    ],
    CS101: [
      {
        id: 'cs101-1',
        title: 'Python 3 Standard Syntax & Operators Cheat Sheet',
        category: 'Cheat Sheets',
        description: 'Essential syntax guide covering data types, slicing, list comprehensions, dictionary operations, and built-in functions.',
        format: 'PDF Guide',
        sizeOrTime: '1.8 MB • 3 pages',
        courseCode: 'CS101',
        badgeColor: 'bg-orange-50 text-orange-700 border-orange-200'
      },
      {
        id: 'cs101-2',
        title: 'Procedural Logic & Control Flow Code Samples',
        category: 'Code Repositories',
        description: 'Hands-on Python scripts showing nested if-else logic, while/for loops with break/continue, and input validation.',
        format: 'Jupyter Notebook',
        sizeOrTime: '8 Notebooks',
        courseCode: 'CS101',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200'
      },
      {
        id: 'cs101-3',
        title: 'Functions, Scopes, and Modular Design Handout',
        category: 'Lecture Notes',
        description: 'In-depth explanation of parameters, return values, variable scope (LEGB rule), lambda functions, and module imports.',
        format: 'Annotated Slides',
        sizeOrTime: '2.9 MB • 24 slides',
        courseCode: 'CS101',
        badgeColor: 'bg-cream-100 text-amber-800 border-amber-200'
      },
      {
        id: 'cs101-4',
        title: 'Python Algorithmic Problem Solving Practice Bank',
        category: 'Practice Sets',
        description: 'Beginner to intermediate programming problems covering string manipulation, math series, and list algorithms.',
        format: 'Problem Set',
        sizeOrTime: '30 Problems',
        courseCode: 'CS101',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200'
      }
    ],
    AI301: [
      {
        id: 'ai301-1',
        title: 'Machine Learning Algorithms & Loss Functions Cheat Sheet',
        category: 'Cheat Sheets',
        description: 'Formulas and quick comparisons for Linear/Logistic Regression, MSE, Cross-Entropy, Decision Trees, and Gradient Descent.',
        format: 'PDF Guide',
        sizeOrTime: '2.7 MB • 5 pages',
        courseCode: 'AI301',
        badgeColor: 'bg-orange-50 text-orange-700 border-orange-200'
      },
      {
        id: 'ai301-2',
        title: 'Scikit-Learn End-to-End Pipeline Repositories',
        category: 'Code Repositories',
        description: 'Complete Python workflows: data preprocessing, train-test splitting, feature scaling, model training, and metric evaluation.',
        format: 'GitHub Repo',
        sizeOrTime: '6 Pipelines',
        courseCode: 'AI301',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200'
      },
      {
        id: 'ai301-3',
        title: 'Model Evaluation & Overfitting Prevention Lecture Pack',
        category: 'Lecture Notes',
        description: 'Comprehensive guide to precision, recall, F1-score, ROC-AUC, bias-variance tradeoff, and L1/L2 regularization.',
        format: 'PDF Notes',
        sizeOrTime: '4.1 MB • 32 slides',
        courseCode: 'AI301',
        badgeColor: 'bg-cream-100 text-amber-800 border-amber-200'
      },
      {
        id: 'ai301-4',
        title: 'Applied Machine Learning Case Study Practice Exercises',
        category: 'Practice Sets',
        description: 'Real-world datasets for classification, regression, and clustering with step-by-step benchmark solutions.',
        format: 'Notebooks + Datasets',
        sizeOrTime: '12 Scenarios',
        courseCode: 'AI301',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200'
      }
    ],
    CS302: [
      {
        id: 'cs302-1',
        title: 'SQL Commands, Joins & Relational Algebra Cheat Sheet',
        category: 'Cheat Sheets',
        description: 'Visual syntax sheet covering INNER/LEFT/RIGHT/FULL JOINs, GROUP BY, HAVING, subqueries, and window functions.',
        format: 'PDF Guide',
        sizeOrTime: '2.1 MB • 4 pages',
        courseCode: 'CS302',
        badgeColor: 'bg-orange-50 text-orange-700 border-orange-200'
      },
      {
        id: 'cs302-2',
        title: 'Schema Normalization (1NF through BCNF) Workbook',
        category: 'Lecture Notes',
        description: 'Formal decomposition exercises, functional dependency analysis, and lossless-join verification examples.',
        format: 'PDF Handout',
        sizeOrTime: '3.4 MB • 22 pages',
        courseCode: 'CS302',
        badgeColor: 'bg-cream-100 text-amber-800 border-amber-200'
      },
      {
        id: 'cs302-3',
        title: 'Sample Relational Database Schema & SQL Scripts',
        category: 'Code Repositories',
        description: 'Complete PostgreSQL/SQLite DDL and DML scripts for university and e-commerce models with complex queries.',
        format: 'SQL Scripts',
        sizeOrTime: '10 Scripts',
        courseCode: 'CS302',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200'
      },
      {
        id: 'cs302-4',
        title: 'Transaction Concurrency, Locking & ACID Exercises',
        category: 'Practice Sets',
        description: 'Practice scenarios on 2PL, serializability schedules, deadlock detection, and recovery logging techniques.',
        format: 'Problem Bank',
        sizeOrTime: '20 Exercises',
        courseCode: 'CS302',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200'
      }
    ]
  };

  const currentResources = allCourseResources[courseCode] || allCourseResources[Object.keys(allCourseResources)[0]] || [];

  const categories = ['All', 'Cheat Sheets', 'Lecture Notes', 'Code Repositories', 'Practice Sets'];

  const filteredResources = currentResources.filter((res) => {
    const matchesCategory = selectedCategory === 'All' || res.category === selectedCategory;
    const matchesSearch =
      searchQuery === '' ||
      res.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_2px_12px_rgba(15,23,42,0.03)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-orange-600 mb-1">
            <BookMarked className="w-4 h-4" />
            <span className="uppercase tracking-wider">Curated Study Materials</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Learning Resources
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Download reference cheat sheets, lecture notes, interactive code, and practice problem sets for your active course.
          </p>
        </div>

        {/* Active Course Badge */}
        <div className="flex items-center space-x-2 px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-orange-500" />
          <span className="text-xs font-bold text-slate-900">{courseTitle}</span>
          <span className="text-slate-400">•</span>
          <span className="text-xs font-semibold text-orange-600 font-mono">{courseCode}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-orange-600 text-white font-semibold shadow-xs'
                  : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Field */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resources, topics..."
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          />
        </div>
      </div>

      {/* Resource Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredResources.map((res) => (
          <div
            key={res.id}
            className="bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs hover:shadow-md hover:border-orange-200 transition-all flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md border ${res.badgeColor}`}>
                  {res.category}
                </span>
                <span className="text-[11px] font-medium text-slate-400">
                  {res.format}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-900 tracking-tight leading-snug">
                  {res.title}
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {res.description}
                </p>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] font-medium text-slate-400">
                {res.sizeOrTime}
              </span>

              <button
                onClick={() => alert(`Opening ${res.title}... Ready for study!`)}
                className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-semibold shadow-xs hover:shadow transition-all cursor-pointer"
              >
                <span>Access Resource</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredResources.length === 0 && (
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-12 text-center text-slate-500 text-xs">
          No resources matched your search filter. Try clearing the search query or selecting "All".
        </div>
      )}
    </div>
  );
};
