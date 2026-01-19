"use client";

import { useState, useEffect } from "react";

// ============================================
// OVERLAY DATA TYPES - Manufacturing Spec
// ============================================

export type LayoutType =
    | 'single-value'
    | 'quick-lookup'
    | 'range-display'
    | 'multi-parameter'
    | 'lookup-with-context'
    | 'alert-information'
    | 'parameter-grid'
    | 'comparison-table';

export interface OverlayData {
    layoutType: LayoutType;
    title: string;
    context?: string;      // Material, machine, wire size
    source?: string;       // Document reference
    data: Record<string, unknown>;
}

// Card width mapping
const cardWidths: Record<LayoutType, string> = {
    'single-value': '350px',
    'quick-lookup': '400px',
    'range-display': '420px',
    'multi-parameter': '460px',
    'lookup-with-context': '480px',
    'alert-information': '500px',
    'parameter-grid': '550px',
    'comparison-table': '650px'
};

interface ManufacturingOverlayProps {
    overlay: OverlayData | null;
    onDismiss: () => void;
}

// ============================================
// MAIN OVERLAY COMPONENT
// ============================================

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

    const cardWidth = cardWidths[overlay.layoutType] || '450px';

    return (
        <div
            className={`
                fixed bottom-10 right-10
                max-w-[90vw] max-h-[calc(100vh-80px)]
                bg-white border border-black
                flex flex-col overflow-hidden
                transition-all duration-300 ease-out
                ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'}
            `}
            style={{
                width: cardWidth,
                fontFamily: 'system-ui, -apple-system, sans-serif',
                borderRadius: 0,
                boxShadow: '6px 6px 0px 0px #000'
            }}
        >
            {/* HEADER - Pink accent, always present */}
            <div
                className="text-black px-6 py-5 flex-shrink-0 border-b border-black"
                style={{ backgroundColor: '#FF0055' }}
            >
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <h3
                            className="text-base font-bold tracking-wide uppercase mb-1"
                            style={{ fontFamily: 'monospace', letterSpacing: '1px' }}
                        >
                            {overlay.title}
                        </h3>
                        {overlay.context && (
                            <p className="text-sm mb-2">{overlay.context}</p>
                        )}
                        {overlay.source && (
                            <p className="text-xs opacity-80 italic">
                                Source: {overlay.source}
                            </p>
                        )}
                    </div>
                    <button
                        onClick={handleDismiss}
                        className="ml-4 w-7 h-7 flex items-center justify-center bg-black text-white hover:bg-gray-800 transition-colors font-bold text-lg"
                        aria-label="Close overlay"
                    >
                        ×
                    </button>
                </div>
            </div>

            {/* BODY - Scrollable content area */}
            <div
                className="p-6 overflow-y-auto flex-1"
                style={{
                    backgroundColor: '#F8F8F6',
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#000 #f4f4f4'
                }}
            >
                {renderContent(overlay)}
            </div>
        </div>
    );
}

// ============================================
// CONTENT RENDERER
// ============================================

function renderContent(overlay: OverlayData) {
    const { layoutType, data } = overlay;

    switch (layoutType) {
        case 'single-value':
            return <SingleValueContent data={data} />;
        case 'quick-lookup':
            return <QuickLookupContent data={data} />;
        case 'range-display':
            return <RangeDisplayContent data={data} />;
        case 'multi-parameter':
            return <MultiParameterContent data={data} />;
        case 'lookup-with-context':
            return <LookupWithContextContent data={data} />;
        case 'alert-information':
            return <AlertInformationContent data={data} />;
        case 'parameter-grid':
            return <ParameterGridContent data={data} />;
        case 'comparison-table':
            return <ComparisonTableContent data={data} />;
        default:
            return <div className="text-sm text-gray-700">{JSON.stringify(data, null, 2)}</div>;
    }
}

// ============================================
// LAYOUT TYPE 1: SINGLE VALUE (350px)
// ============================================

function SingleValueContent({ data }: { data: Record<string, unknown> }) {
    const value = (data.value as string) || '';
    const label = (data.label as string) || '';
    const range = (data.range as string) || '';
    const tolerance = (data.tolerance as string) || '';

    return (
        <div className="text-center py-6">
            <p
                className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2"
                style={{ fontFamily: 'monospace' }}
            >
                {label}
            </p>
            <p className="text-5xl font-extrabold text-black mb-4 leading-none">
                {value}
            </p>
            {range && (
                <div
                    className="inline-block bg-white px-5 py-3 border border-black"
                    style={{ boxShadow: '3px 3px 0px 0px #000' }}
                >
                    <p className="text-sm text-black">
                        Acceptable Range: <span className="font-semibold">{range}</span>
                    </p>
                </div>
            )}
            {tolerance && (
                <p className="mt-4 text-sm text-gray-600">
                    Tolerance: {tolerance}
                </p>
            )}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 2: QUICK LOOKUP (400px)
// ============================================

function QuickLookupContent({ data }: { data: Record<string, unknown> }) {
    const wireSize = (data.wire_size as string) || '';
    const values = (data.values as Record<string, string>) || {};
    const adjacent = (data.adjacent as string[]) || [];

    return (
        <div className="space-y-4">
            {wireSize && (
                <p className="text-sm text-gray-600">
                    Wire Size: <span className="font-semibold text-black">{wireSize}</span>
                </p>
            )}

            {/* Main values box */}
            <div
                className="bg-white p-4 border border-black"
                style={{ boxShadow: '3px 3px 0px 0px #000' }}
            >
                {Object.entries(values).map(([key, val]) => (
                    <div key={key} className="py-2 border-b border-gray-200 last:border-b-0">
                        <span className="font-semibold text-black">{key}:</span>{' '}
                        <span className="text-gray-700">{val}</span>
                    </div>
                ))}
            </div>

            {/* Adjacent info */}
            {adjacent.length > 0 && (
                <div>
                    <p
                        className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2"
                        style={{ fontFamily: 'monospace' }}
                    >
                        Adjacent Wire Sizes:
                    </p>
                    <ul className="space-y-1">
                        {adjacent.map((item, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-start">
                                <span className="mr-2">•</span>
                                <span>{item}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 3: RANGE DISPLAY (420px)
// ============================================

function RangeDisplayContent({ data }: { data: Record<string, unknown> }) {
    const target = (data.target as string) || '';
    const minimum = (data.minimum as string) || '';
    const maximum = (data.maximum as string) || '';
    const tolerance = (data.tolerance as string) || '';
    const notes = (data.notes as string[]) || [];

    return (
        <div className="space-y-4">
            {/* Target */}
            <div className="text-center">
                <p
                    className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1"
                    style={{ fontFamily: 'monospace' }}
                >
                    Target Temperature
                </p>
                <p className="text-4xl font-extrabold text-black">{target}</p>
            </div>

            {/* Range box */}
            <div
                className="bg-white p-4 border border-black"
                style={{ boxShadow: '3px 3px 0px 0px #000' }}
            >
                <p
                    className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3"
                    style={{ fontFamily: 'monospace' }}
                >
                    Acceptable Range
                </p>
                <div className="space-y-2">
                    <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Minimum:</span>
                        <span className="text-sm font-semibold text-black">{minimum}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Target:</span>
                        <span className="text-sm font-semibold text-black">{target} ← Standard</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Maximum:</span>
                        <span className="text-sm font-semibold text-black">{maximum}</span>
                    </div>
                </div>
            </div>

            {tolerance && (
                <p className="text-sm text-gray-600 text-center">
                    Tolerance: <span className="font-semibold">{tolerance}</span>
                </p>
            )}

            {/* Notes */}
            {notes.length > 0 && notes.map((note, idx) => (
                <p key={idx} className="text-sm text-gray-600">{note}</p>
            ))}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 4: MULTI-PARAMETER (460px)
// ============================================

function MultiParameterContent({ data }: { data: Record<string, unknown> }) {
    const parameters = (data.parameters as Array<{
        name: string;
        target?: string;
        range?: string;
        tolerance?: string;
    }>) || [];
    const note = (data.note as string) || '';

    return (
        <div className="space-y-4">
            {parameters.map((param, idx) => (
                <div
                    key={idx}
                    className="bg-white p-4 border border-black"
                    style={{ boxShadow: '3px 3px 0px 0px #000' }}
                >
                    <p
                        className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2"
                        style={{ fontFamily: 'monospace' }}
                    >
                        {param.name}
                    </p>
                    {param.target && (
                        <p className="text-sm">
                            <span className="text-gray-600">Target:</span>{' '}
                            <span className="font-semibold text-black">{param.target}</span>
                        </p>
                    )}
                    {param.range && (
                        <p className="text-sm">
                            <span className="text-gray-600">Range:</span>{' '}
                            <span className="font-semibold text-black">{param.range}</span>
                        </p>
                    )}
                    {param.tolerance && (
                        <p className="text-sm">
                            <span className="text-gray-600">Tolerance:</span>{' '}
                            <span className="font-semibold text-black">{param.tolerance}</span>
                        </p>
                    )}
                </div>
            ))}

            {note && (
                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-3">
                    <p className="text-sm text-gray-800 font-medium">{note}</p>
                </div>
            )}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 5: LOOKUP WITH CONTEXT (480px)
// ============================================

function LookupWithContextContent({ data }: { data: Record<string, unknown> }) {
    const wireSize = (data.wire_size as string) || '';
    const main = (data.main as Record<string, string>) || {};
    const previous = (data.previous as { range: string; values: Record<string, string> }) || null;
    const next = (data.next as { range: string; values: Record<string, string> }) || null;
    const note = (data.note as string) || '';

    return (
        <div className="space-y-4">
            {wireSize && (
                <p className="text-sm text-gray-600">
                    Wire Size: <span className="font-semibold text-black">{wireSize}</span>
                </p>
            )}

            {/* Main values box */}
            <div
                className="bg-white p-4 border border-black"
                style={{ boxShadow: '3px 3px 0px 0px #000' }}
            >
                {Object.entries(main).map(([key, val]) => (
                    <div key={key} className="py-2 border-b border-gray-200 last:border-b-0">
                        <span className="font-semibold text-black">{key}:</span>{' '}
                        <span className="text-gray-700">{val}</span>
                    </div>
                ))}
            </div>

            {/* Adjacent wire sizes */}
            <div>
                <p
                    className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3"
                    style={{ fontFamily: 'monospace' }}
                >
                    Adjacent Wire Sizes:
                </p>

                {previous && (
                    <div className="mb-3">
                        <p className="text-sm font-semibold text-gray-700 mb-1">
                            Previous ({previous.range}):
                        </p>
                        <ul className="space-y-1 ml-4">
                            {Object.entries(previous.values).map(([k, v]) => (
                                <li key={k} className="text-sm text-gray-600">
                                    • {k}: {v}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {next && (
                    <div>
                        <p className="text-sm font-semibold text-gray-700 mb-1">
                            Next ({next.range}):
                        </p>
                        <ul className="space-y-1 ml-4">
                            {Object.entries(next.values).map(([k, v]) => (
                                <li key={k} className="text-sm text-gray-600">
                                    • {k}: {v}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {note && (
                <div className="bg-pink-50 border-l-4 p-3" style={{ borderColor: '#FF0055' }}>
                    <p className="text-sm text-gray-800">💡 {note}</p>
                </div>
            )}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 6: ALERT INFORMATION (500px)
// ============================================

function AlertInformationContent({ data }: { data: Record<string, unknown> }) {
    const warning = (data.warning as string) || '';
    const donts = (data.donts as string[]) || [];
    const dos = (data.dos as string[]) || [];
    const reference = (data.reference as string) || '';

    return (
        <div
            className="bg-white border-2 border-black p-5"
            style={{
                borderLeftWidth: '6px',
                borderLeftColor: '#FF0055',
                boxShadow: '4px 4px 0px 0px #000'
            }}
        >
            {/* Warning icon */}
            <div className="text-center text-4xl mb-4">⚠️</div>

            {/* Main warning */}
            {warning && (
                <p
                    className="text-base font-bold text-center text-black uppercase tracking-wide mb-4"
                    style={{ fontFamily: 'monospace' }}
                >
                    🚫 {warning}
                </p>
            )}

            {/* Don'ts */}
            {donts.length > 0 && (
                <div className="mb-4">
                    <p className="text-sm font-bold text-black mb-2">Critical Differences:</p>
                    {donts.map((item, idx) => (
                        <div key={idx} className="py-1.5 text-sm text-black flex items-start">
                            <span className="mr-2 font-bold">❌</span>
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Dos */}
            {dos.length > 0 && (
                <div className="mb-4">
                    {dos.map((item, idx) => (
                        <div key={idx} className="py-1.5 text-sm text-black flex items-start">
                            <span className="mr-2 font-bold">✅</span>
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Reference note */}
            {reference && (
                <p className="text-sm text-gray-600 italic mt-4">
                    Reference: "{reference}"
                </p>
            )}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 7: PARAMETER GRID (550px)
// ============================================

function ParameterGridContent({ data }: { data: Record<string, unknown> }) {
    const zones = (data.zones as Array<{
        name: string;
        value: string;
        range?: string;
    }>) || [];
    const auxiliary = (data.auxiliary as string[]) || [];
    const notes = (data.notes as string[]) || [];

    // Split into rows of 3
    const rows: Array<Array<typeof zones[0]>> = [];
    for (let i = 0; i < zones.length; i += 3) {
        rows.push(zones.slice(i, i + 3));
    }

    return (
        <div className="space-y-4">
            <p
                className="text-xs font-bold text-gray-500 uppercase tracking-wide"
                style={{ fontFamily: 'monospace' }}
            >
                Zone Temperatures (°C):
            </p>

            {/* Grid rows */}
            {rows.map((row, rowIdx) => (
                <div key={rowIdx} className="grid grid-cols-3 gap-4">
                    {row.map((zone, idx) => (
                        <div
                            key={idx}
                            className="bg-white p-4 border border-black text-center"
                            style={{ boxShadow: '3px 3px 0px 0px #000' }}
                        >
                            <p
                                className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1"
                                style={{ fontFamily: 'monospace' }}
                            >
                                {zone.name}
                            </p>
                            <p className="text-2xl font-extrabold text-black">
                                {zone.value}
                            </p>
                            {zone.range && (
                                <p className="text-xs text-gray-500 mt-1">{zone.range}</p>
                            )}
                        </div>
                    ))}
                </div>
            ))}

            {/* Auxiliary Settings */}
            {auxiliary.length > 0 && (
                <div className="bg-pink-50 border-l-4 p-4" style={{ borderColor: '#FF0055' }}>
                    <p
                        className="text-xs font-bold text-black uppercase tracking-wide mb-2"
                        style={{ fontFamily: 'monospace' }}
                    >
                        Auxiliary Settings
                    </p>
                    <ul className="space-y-1">
                        {auxiliary.map((item, idx) => (
                            <li key={idx} className="text-sm text-gray-800">• {item}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Notes */}
            {notes.length > 0 && notes.map((note, idx) => (
                <div key={idx} className="bg-yellow-50 border-l-4 border-yellow-500 p-3">
                    <p className="text-sm text-gray-800 font-medium">{note}</p>
                </div>
            ))}
        </div>
    );
}

// ============================================
// LAYOUT TYPE 8: COMPARISON TABLE (650px)
// ============================================

function ComparisonTableContent({ data }: { data: Record<string, unknown> }) {
    const columns = (data.columns as string[]) || [];
    const rows = (data.rows as Array<Record<string, string>>) || [];
    const analysis = (data.analysis as string) || '';
    const additional = (data.additional as string[]) || [];

    return (
        <div className="space-y-4">
            {/* Table */}
            <div className="overflow-x-auto">
                <table
                    className="w-full text-sm border border-black"
                    style={{ borderCollapse: 'collapse' }}
                >
                    <thead style={{ backgroundColor: '#FF0055' }}>
                        <tr>
                            {columns.map((col, idx) => (
                                <th
                                    key={idx}
                                    className="px-3 py-2.5 text-left font-bold text-black border-r border-black last:border-r-0"
                                    style={{
                                        fontFamily: 'monospace',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em'
                                    }}
                                >
                                    {col}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white">
                        {rows.map((row, rowIdx) => (
                            <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                                {columns.map((col, colIdx) => (
                                    <td
                                        key={colIdx}
                                        className="px-3 py-2.5 border-b border-black border-r border-gray-200 last:border-r-0"
                                    >
                                        {row[col] || '-'}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Additional info */}
            {additional.length > 0 && (
                <div>
                    {additional.map((item, idx) => (
                        <p key={idx} className="text-sm text-gray-700 mb-1">• {item}</p>
                    ))}
                </div>
            )}

            {/* Analysis */}
            {analysis && (
                <div className="bg-pink-50 border-l-4 p-3" style={{ borderColor: '#FF0055' }}>
                    <p className="text-sm text-gray-800">💡 {analysis}</p>
                </div>
            )}
        </div>
    );
}