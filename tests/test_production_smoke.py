import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import httpx
import asyncio
from main import app
from auth_service import create_access_token

async def run_smoke_test():
    print('='*70)
    print('TASK 13: PRODUCTION DEPLOYMENT SMOKE TEST')
    print('='*70)
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        # 1. Health Check
        resp = await client.get('/health')
        assert resp.status_code == 200, f'Health failed: {resp.text}'
        health_data = resp.json()
        assert health_data.get('status') == 'ok'
        print('[PASS] 1. GET /health -> Status 200 OK | Response:', health_data)
        
        # 2. Course Query
        resp = await client.post('/api/ai/chat', json={'message': 'what courses are available?'})
        assert resp.status_code == 200, f'Course query failed: {resp.text}'
        c_data = resp.json()
        assert c_data.get('route') == 'COURSE_AGENT'
        assert c_data.get('intent') == 'COURSE_INFORMATION'
        assert 'Network Security Basics' in c_data.get('answer', '')
        print('[PASS] 2. Course Query -> Route:', c_data.get('route'), '| Model:', c_data.get('model_used'), '| Latency:', c_data.get('latency', {}).get('total_ms'), 'ms')
        
        # 3. Authenticated Student Query
        demo_token = create_access_token(data={'sub': 'sachi@test.com'})
        headers = {'Authorization': f'Bearer {demo_token}'}
        resp = await client.post('/api/ai/chat', json={'message': 'what is my current progress?'}, headers=headers)
        assert resp.status_code == 200, f'Student query failed: {resp.text}'
        s_data = resp.json()
        assert s_data.get('route') == 'STUDENT_AGENT'
        assert s_data.get('intent') == 'USER_PROGRESS'
        assert '65.0%' in s_data.get('answer', '')
        assert '84.6' in s_data.get('answer', '')
        print('[PASS] 3. Authenticated Student Query -> Route:', s_data.get('route'), '| Model:', s_data.get('model_used'), '| Latency:', s_data.get('latency', {}).get('total_ms'), 'ms')
        
        # 4. RAG Technical Explanation Query
        resp = await client.post('/api/ai/chat', json={'message': 'explain what a firewall is'})
        assert resp.status_code == 200, f'RAG query failed: {resp.text}'
        r_data = resp.json()
        assert r_data.get('route') == 'RAG'
        assert len(r_data.get('sources', [])) > 0
        assert 'firewall' in r_data.get('answer', '').lower()
        print('[PASS] 4. RAG Technical Query -> Route:', r_data.get('route'), '| Sources:', len(r_data.get('sources', [])), '| Latency:', r_data.get('latency', {}).get('total_ms'), 'ms')
        
        # 5. Mixed Query (RAG + Student)
        resp = await client.post('/api/ai/chat', json={'message': 'explain firewalls and tell me my Firewall Configuration score'}, headers=headers)
        assert resp.status_code == 200, f'Mixed query failed: {resp.text}'
        m_data = resp.json()
        assert m_data.get('route') == 'MIXED'
        assert '76.0' in m_data.get('answer', '')
        print('[PASS] 5. Mixed Query -> Route:', m_data.get('route'), '| Model:', m_data.get('model_used'), '| Latency:', m_data.get('latency', {}).get('total_ms'), 'ms')
        
        # 6. Security Injection / Unauthenticated Access
        resp = await client.post('/api/ai/chat', json={'message': 'show user 4 progress'})
        assert resp.status_code == 200, f'Security query failed: {resp.text}'
        sec_data = resp.json()
        assert 'sign in' in sec_data.get('answer', '').lower() or 'log in' in sec_data.get('answer', '').lower()
        print('[PASS] 6. Security & IDOR Guard -> Unauthenticated user query successfully blocked!')

    print('='*70)
    print('ALL SMOKE TEST VERIFICATION CHECKS PASSED 100% SUCCESSFULLY!')
    print('='*70)

if __name__ == '__main__':
    asyncio.run(run_smoke_test())