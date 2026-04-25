"""
Mock MiroFish Backend for Local Testing
Simulates multi-agent simulator responses
"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'mirofish-mock',
        'version': '0.1.0'
    }), 200

@app.route('/api/graph/build', methods=['POST'])
def graph_build():
    """Mock graph build endpoint - matches client.py line 109"""
    data = request.get_json()
    project_id = f"proj_{data.get('project_name', 'xprclaw')}"
    return jsonify({
        'project_id': project_id,
        'status': 'success',
        'nodes': 5,
        'edges': 12
    }), 200

@app.route('/api/graph/status/<project_id>', methods=['GET'])
def graph_status(project_id):
    """Mock graph status endpoint - matches client.py line 116"""
    return jsonify({
        'project_id': project_id,
        'status': 'ready',
        'progress': 100
    }), 200

@app.route('/api/simulation/prepare', methods=['POST'])
def simulation_prepare():
    """Mock simulation prepare endpoint - matches client.py line 126"""
    data = request.get_json()
    simulation_id = f"sim_{data.get('project_id', 'unknown')}"
    return jsonify({
        'simulation_id': simulation_id,
        'status': 'prepared',
        'personas': len(data.get('personas', []))
    }), 200

@app.route('/api/simulation/start', methods=['POST'])
def simulation_start():
    """Mock simulation start endpoint - matches client.py line 140"""
    data = request.get_json()
    return jsonify({
        'simulation_id': data.get('simulation_id', 'sim_unknown'),
        'status': 'started'
    }), 200

@app.route('/api/simulation/status/<simulation_id>', methods=['GET'])
def simulation_status(simulation_id):
    """Mock simulation status endpoint - matches client.py line 150"""
    return jsonify({
        'simulation_id': simulation_id,
        'status': 'completed',
        'rounds_completed': 30,
        'results_ready': True
    }), 200

@app.route('/api/simulation/<simulation_id>/results', methods=['GET'])
def simulation_results(simulation_id):
    """Mock simulation results endpoint - matches client.py line 156"""
    return jsonify({
        'simulation_id': simulation_id,
        'agents': {
            'lda': {'decision': 'proceed', 'confidence': 0.8, 'rationale': 'LDA: Positive momentum detected'},
            'daa': {'decision': 'hold', 'confidence': 0.6, 'rationale': 'DAA: Waiting for confirmation'},
            'kyc_a': {'decision': 'proceed', 'confidence': 0.75, 'rationale': 'KYC-A: Risk profile acceptable'},
            'efa': {'decision': 'reduce', 'confidence': 0.65, 'rationale': 'EFA: Some volatility signals'},
            'rea': {'decision': 'proceed', 'confidence': 0.85, 'rationale': 'REA: Revenue expectations strong'},
        },
        'final_verdict': 'proceed',
        'confidence': 0.73
    }), 200

@app.route('/simulate', methods=['POST'])
def simulate():
    """Simulate market analysis with 5 agents"""
    data = request.get_json()

    # Mock agent opinions (5 agents voting)
    agents = {
        'lda': {'decision': 'proceed', 'confidence': 0.8, 'rationale': 'LDA: Positive momentum detected'},
        'daa': {'decision': 'hold', 'confidence': 0.6, 'rationale': 'DAA: Waiting for confirmation'},
        'kyc_a': {'decision': 'proceed', 'confidence': 0.75, 'rationale': 'KYC-A: Risk profile acceptable'},
        'efa': {'decision': 'reduce', 'confidence': 0.65, 'rationale': 'EFA: Some volatility signals'},
        'rea': {'decision': 'proceed', 'confidence': 0.85, 'rationale': 'REA: Revenue expectations strong'},
    }

    # Tally votes
    decisions = [a['decision'] for a in agents.values()]
    confidences = [a['confidence'] for a in agents.values()]

    # Majority vote
    from collections import Counter
    vote_count = Counter(decisions)
    final_decision = vote_count.most_common(1)[0][0]
    final_confidence = sum(confidences) / len(confidences)

    return jsonify({
        'recommendation': {
            'action': final_decision,
            'confidence': final_confidence,
            'rationale': f'Merged {len(agents)} agent opinions: {", ".join([f"{k}={v["decision"]}" for k,v in agents.items()])}'
        },
        'agents': agents,
        'verdict': {
            'proceed_votes': decisions.count('proceed'),
            'hold_votes': decisions.count('hold'),
            'reduce_votes': decisions.count('reduce'),
            'abort_votes': decisions.count('abort'),
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
