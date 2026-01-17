"use client";

import { useState, useEffect } from "react";

// Overlay data types matching manufacturing specifications
export interface OverlayData {
    type: 'temperature-profile' | 'corrective-action' | 'quality-verification' | 'documentation-checklist' | 'knowledge-summary';
    title: string;
    subtitle?: string;
    source?: string;
    data: Record<string, unknown>;
}

interface ManufacturingOverlayProps {
    overlay: OverlayData | null;
    onDismiss: () => void;
}

export function ManufacturingOverlay({ overlay, onDismiss }: ManufacturingOverlayProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (overlay) {
            requestAnimationFrame(() => setIsVisible(true));
        } else {
            setIsVisible(false);
        }
    }, [overlay]);

    if (!overlay) return null;

    const handleDismiss = () => {
        setIsVisible(false);
        setTimeout(onDismiss, 300);
    };

    return (
        <div
            className={`
                fixed top-1/2 right-8 -translate-y-1/2
                w-[750px] max-w-[90vw] max-h-[600px]
                bg-white border-2 border-gray-800
                shadow-[8px_8px_0px_0px_rgba(0,0,0,0.3)]
                flex flex-col overflow-hidden
                transition-all duration-300 ease-out
                ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'}
            `}
            style={{
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}
        >
            {/* Header - 60px height */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 border-b-2 border-gray-800 flex-shrink-0">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <h3 className="text-lg font-bold tracking-wide">
                            {overlay.title}
                        </h3>
                        {overlay.subtitle && (
                            <p className="text-sm mt-0.5 opacity-90">{overlay.subtitle}</p>
                        )}
                    </div>
                    <button
                        onClick={handleDismiss}
                        className="ml-4 w-7 h-7 flex items-center justify-center bg-white text-gray-800 hover:bg-gray-100 transition-colors font-bold text-lg rounded"
                        aria-label="Close overlay"
                    >
                        ×
                    </button>
                </div>
            </div>

            {/* Body - Scrollable content area, max 440px */}
            <div className="p-6 overflow-y-auto flex-1 bg-gray-50" style={{ maxHeight: '440px' }}>
                {renderContent(overlay)}
            </div>

            {/* Footer - 50px height */}
            {overlay.source && (
                <div className="px-6 py-3 border-t-2 border-gray-200 bg-white flex-shrink-0">
                    <p className="text-xs text-gray-600">
                        <span className="font-semibold">Reference:</span> {overlay.source}
                    </p>
                </div>
            )}
        </div>
    );
}

function renderContent(overlay: OverlayData) {
    const { type, data } = overlay;

    switch (type) {
        case 'temperature-profile':
            return <TemperatureProfileContent data={data} />;
        case 'corrective-action':
            return <CorrectiveActionContent data={data} />;
        case 'quality-verification':
            return <QualityVerificationContent data={data} />;
        case 'documentation-checklist':
            return <DocumentationChecklistContent data={data} />;
        case 'knowledge-summary':
            return <KnowledgeSummaryContent data={data} />;
        default:
            return <div className="text-sm text-gray-700">{JSON.stringify(data, null, 2)}</div>;
    }
}

// -------------------------
// TEMPERATURE PROFILE
// -------------------------
function TemperatureProfileContent({ data }: { data: Record<string, unknown> }) {
    const rows = (data.rows as Array<{ zone: string; temperature: string; section: string }>) || [];
    const auxiliary = (data.auxiliary as string) || '';
    const notes = (data.notes as string) || '';

    return (
        <div className="space-y-4">
            {/* Temperature Table - Max 8 rows */}
            {rows.length > 0 && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-2">Temperature Zones</h4>
                    <table className="w-full text-sm border-2 border-gray-300">
                        <thead className="bg-blue-600 text-white">
                            <tr>
                                <th className="px-3 py-2 text-left font-semibold border-r border-gray-400">Zone</th>
                                <th className="px-3 py-2 text-left font-semibold border-r border-gray-400">Temperature</th>
                                <th className="px-3 py-2 text-left font-semibold">Section</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white">
                            {rows.slice(0, 8).map((row, index) => (
                                <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                                    <td className="px-3 py-2 font-semibold border-r border-gray-200">{row.zone}</td>
                                    <td className="px-3 py-2 border-r border-gray-200">{row.temperature}</td>
                                    <td className="px-3 py-2 text-gray-600">{row.section}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Auxiliary Parameters - Max 6 items */}
            {auxiliary && (
                <div className="bg-blue-50 border-l-4 border-blue-600 p-4">
                    <h4 className="text-base font-bold text-gray-900 mb-2">Auxiliary Settings</h4>
                    <div className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">
                        {auxiliary}
                    </div>
                </div>
            )}

            {/* Notes - Max 3 items */}
            {notes && (
                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4">
                    <div className="text-sm text-gray-800 whitespace-pre-line font-medium">
                        {notes}
                    </div>
                </div>
            )}
        </div>
    );
}

// -------------------------
// CORRECTIVE ACTION
// -------------------------
function CorrectiveActionContent({ data }: { data: Record<string, unknown> }) {
    const steps = (data.steps as Array<{ number: number; action: string; details: string[] }>) || [];
    const safetyLimits = (data.safety_limits as string) || '';

    return (
        <div className="space-y-4">
            <div className="bg-blue-50 border-l-4 border-blue-600 p-3">
                <p className="text-sm font-semibold text-gray-900">RECOMMENDED SOLUTION</p>
            </div>

            {/* Steps - Max 4 steps */}
            {steps.slice(0, 4).map((step, index) => (
                <div key={index} className="space-y-2">
                    <h4 className="text-base font-bold text-gray-900">
                        Step {step.number}: {step.action}
                    </h4>
                    <ul className="space-y-1 ml-4">
                        {step.details.slice(0, 4).map((detail, detailIndex) => (
                            <li key={detailIndex} className="text-sm text-gray-700 flex items-start">
                                <span className="mr-2">•</span>
                                <span>{detail}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            ))}

            {/* Safety Limits - Single line */}
            {safetyLimits && (
                <div className="bg-yellow-50 border-2 border-yellow-400 p-4 mt-4">
                    <p className="text-sm font-bold text-gray-900 mb-1">⚠️ CRITICAL SAFETY LIMITS:</p>
                    <p className="text-sm text-gray-800 font-medium">{safetyLimits}</p>
                </div>
            )}
        </div>
    );
}

// -------------------------
// QUALITY VERIFICATION
// -------------------------
function QualityVerificationContent({ data }: { data: Record<string, unknown> }) {
    const spec = (data.spec as string) || '';
    const range = (data.range as string) || '';
    const measurements = (data.measurements as Array<{ point: string; reading: string; status: string }>) || [];
    const statistics = (data.statistics as string) || '';
    const verdict = (data.verdict as string) || '';
    const verdictIcon = (data.verdict_icon as string) || '';

    return (
        <div className="space-y-4">
            {/* Specification - Single line */}
            {spec && (
                <div className="bg-gray-100 p-3 border-l-4 border-gray-600">
                    <p className="text-sm font-semibold text-gray-900">SPECIFICATION</p>
                    <p className="text-sm text-gray-700 mt-1">{spec}</p>
                    {range && <p className="text-sm text-gray-700">{range}</p>}
                </div>
            )}

            {/* Measurements Table - Max 5 rows */}
            {measurements.length > 0 && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-2">Measurements</h4>
                    <table className="w-full text-sm border-2 border-gray-300">
                        <thead className="bg-green-600 text-white">
                            <tr>
                                <th className="px-3 py-2 text-left font-semibold border-r border-gray-400">Point</th>
                                <th className="px-3 py-2 text-left font-semibold border-r border-gray-400">Reading</th>
                                <th className="px-3 py-2 text-left font-semibold">Status</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white">
                            {measurements.slice(0, 5).map((measurement, index) => (
                                <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                                    <td className="px-3 py-2 border-r border-gray-200">{measurement.point}</td>
                                    <td className="px-3 py-2 font-semibold border-r border-gray-200">{measurement.reading}</td>
                                    <td className="px-3 py-2">
                                        <span className={`inline-flex items-center px-2 py-1 text-xs font-bold rounded ${measurement.status === 'pass'
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-red-100 text-red-800'
                                            }`}>
                                            {measurement.status === 'pass' ? '✓ PASS' : '✗ FAIL'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Statistics - Single line */}
            {statistics && (
                <p className="text-sm text-gray-700 font-medium">{statistics}</p>
            )}

            {/* Verdict */}
            {verdict && (
                <div className={`p-4 border-2 text-center ${verdict.includes('WITHIN')
                        ? 'bg-green-50 border-green-500'
                        : 'bg-red-50 border-red-500'
                    }`}>
                    <p className="text-lg font-bold text-gray-900">
                        {verdictIcon} {verdict}
                    </p>
                </div>
            )}
        </div>
    );
}

// -------------------------
// DOCUMENTATION CHECKLIST
// -------------------------
function DocumentationChecklistContent({ data }: { data: Record<string, unknown> }) {
    const autoCaptured = (data.auto_captured as Array<{ label: string; value: string }>) || [];
    const manualRequired = (data.manual_required as string[]) || [];
    const locationDigital = (data.location_digital as string) || '';
    const locationPaper = (data.location_paper as string) || '';
    const deadline = (data.deadline as string) || '';

    return (
        <div className="space-y-4">
            {/* Auto-captured - Max 8 items */}
            {autoCaptured.length > 0 && (
                <div>
                    <h4 className="text-base font-bold text-green-700 mb-2">
                        ✓ AUTO-LOGGED (from conversation)
                    </h4>
                    <div className="bg-green-50 border-l-4 border-green-600 p-3 space-y-1">
                        {autoCaptured.slice(0, 8).map((item, index) => (
                            <div key={index} className="text-sm">
                                <span className="font-semibold text-gray-900">{item.label}:</span>{' '}
                                <span className="text-gray-700">{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Manual required - Max 5 items */}
            {manualRequired.length > 0 && (
                <div>
                    <h4 className="text-base font-bold text-orange-700 mb-2">
                        YOU MUST ADD
                    </h4>
                    <div className="bg-orange-50 border-l-4 border-orange-600 p-3">
                        <ul className="space-y-1">
                            {manualRequired.slice(0, 5).map((item, index) => (
                                <li key={index} className="text-sm text-gray-800 flex items-start">
                                    <span className="mr-2">•</span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Where to log - 2 lines max */}
            {(locationDigital || locationPaper) && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-2">📍 WHERE TO LOG</h4>
                    <div className="bg-blue-50 border-l-4 border-blue-600 p-3 space-y-1">
                        {locationDigital && (
                            <p className="text-sm text-gray-800">
                                <span className="font-semibold">Digital:</span> {locationDigital}
                            </p>
                        )}
                        {locationPaper && (
                            <p className="text-sm text-gray-800">
                                <span className="font-semibold">Paper:</span> {locationPaper}
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* Deadline */}
            {deadline && (
                <div className="bg-yellow-50 border-2 border-yellow-400 p-3 text-center">
                    <p className="text-sm font-bold text-gray-900">⏰ {deadline}</p>
                </div>
            )}
        </div>
    );
}

// -------------------------
// KNOWLEDGE SUMMARY
// -------------------------
function KnowledgeSummaryContent({ data }: { data: Record<string, unknown> }) {
    const problem = (data.problem as string) || '';
    const rootCause = (data.root_cause as string) || '';
    const solution = (data.solution as string) || '';
    const learnings = (data.learnings as Array<{ number: string; title: string; lesson: string }>) || [];
    const quickReference = (data.quick_reference as string) || '';

    return (
        <div className="space-y-4">
            {/* Problem - 2 lines max */}
            {problem && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-1">PROBLEM</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{problem}</p>
                </div>
            )}

            {/* Root Cause - 2 lines max */}
            {rootCause && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-1">ROOT CAUSE</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{rootCause}</p>
                </div>
            )}

            {/* Solution - 2 lines max */}
            {solution && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-1">SOLUTION APPLIED</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{solution}</p>
                </div>
            )}

            {/* Key Learnings - Max 3 points, 2 lines each */}
            {learnings.length > 0 && (
                <div>
                    <h4 className="text-base font-bold text-gray-900 mb-2">KEY LEARNING POINTS</h4>
                    <div className="space-y-3">
                        {learnings.slice(0, 3).map((learning, index) => (
                            <div key={index} className="bg-purple-50 border-l-4 border-purple-600 p-3">
                                <p className="text-sm font-bold text-gray-900 mb-1">
                                    {learning.number} {learning.title}
                                </p>
                                <p className="text-sm text-gray-700 leading-relaxed">{learning.lesson}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick Reference - 3 lines max */}
            {quickReference && (
                <div className="bg-blue-50 border-2 border-blue-400 p-3">
                    <h4 className="text-sm font-bold text-gray-900 mb-1">⚡ QUICK REFERENCE</h4>
                    <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-line">{quickReference}</p>
                </div>
            )}
        </div>
    );
}