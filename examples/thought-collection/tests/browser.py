from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def run():
    assert (ROOT/'index.html').exists(), 'Build a standalone HTML first'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
        ctx.set_offline(True)
        page=ctx.new_page(); errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((ROOT/'index.html').as_uri());page.wait_for_function('window.ready===true')
        assert page.locator('.tile').count()==0
        page.locator('#demo').click()
        assert page.locator('.tile').count()==5
        page.locator('.note-menu').first.click()
        page.locator('[data-action="color"]').click()
        page.locator('[data-color="mint"]').click()
        page.locator('#submit-sheet').click()
        assert page.locator('#home').is_visible(), 'Quick menu changes must not open detail behind the sheet'
        page.locator('#undo').click()
        page.locator('#toast').evaluate("el=>el.classList.remove('show')")
        page.screenshot(path=str(ROOT/'home-browser.png'))
        page.locator('.open-note').first.click()
        page.screenshot(path=str(ROOT/'detail-browser.png'))
        page.locator('[data-action="addition"]').click()
        page.locator('#entry-text').fill('今天补充的内容')
        page.locator('#submit-sheet').click()
        assert page.locator('#detail').inner_text().count('今天补充的内容')==1
        page.locator('[data-action="wording"]').click()
        page.locator('#entry-text').fill('先验证一周，再决定是否继续')
        page.locator('#submit-sheet').click()
        page.locator('[data-action="compare"]').click()
        assert '这个项目到底要不要继续' in page.locator('#sheet').inner_text()
        assert '先验证一周，再决定是否继续' in page.locator('#sheet').inner_text()
        page.locator('#close-sheet').click()
        page.locator('[data-action="split"]').click()
        page.locator('[data-child]').nth(0).fill('第一条自己写的子念头')
        page.locator('[data-child]').nth(1).fill('第二条自己写的子念头')
        page.locator('#submit-sheet').click()
        assert page.evaluate('window.thoughtApp.state.notes.length')==7
        page.locator('[data-action="relate"]').click()
        page.locator('#link-target').select_option(index=1)
        page.locator('#link-reason').fill('这两件事想一起看')
        page.locator('#submit-sheet').click()
        assert '这两件事想一起看' in page.locator('#detail').inner_text()
        page.locator('[data-action="public"]').click()
        assert page.locator('#public-text').input_value()==''
        page.locator('#public-text').fill('只公开这一句，不带入私人历史。')
        page.locator('#public-text').dispatch_event('input')
        with page.expect_download() as dl: page.locator('#download-card').click()
        out=ROOT/'public-card-test.png';dl.value.save_as(str(out))
        from PIL import Image
        assert Image.open(out).size==(1200,1600)
        assert page.evaluate('window.thoughtApp.state.notes[0].versions[0].text')=='这个项目到底要不要继续'
        page.locator('#close-sheet').click()
        page.locator('#detail-more').click()
        page.locator('[data-action="trash"]').click()
        assert page.evaluate('window.thoughtApp.state.notes[0].lifecycle')=='trash'
        page.locator('#undo').click()
        assert page.evaluate('window.thoughtApp.state.notes[0].lifecycle')=='active'
        page.locator('#exit-demo').click()
        assert page.locator('.tile').count()==0, 'Demo must not mix into private collection'
        page.locator('#new-note').click();page.locator('#entry-text').fill('尚未提交的私人草稿')
        page.locator('#close-sheet').click();page.locator('#demo').click();page.locator('#new-note').click()
        assert page.locator('#entry-text').input_value()=='', 'Demo must not expose private drafts'
        page.locator('#entry-text').fill('仅在示例中的新增');page.locator('#submit-sheet').click()
        page.locator('#exit-demo').click();page.locator('#new-note').click()
        assert page.locator('#entry-text').input_value()=='尚未提交的私人草稿', 'Private draft must survive demo editing'
        page.locator('#close-sheet').click()
        page.locator('#new-note').click()
        page.locator('#entry-text').fill('我自己的第一条念头')
        page.locator('#submit-sheet').click()
        page.reload();page.wait_for_function('window.ready===true')
        assert page.locator('.tile').count()==1
        assert '我自己的第一条念头' in page.locator('#home').inner_text()
        page.evaluate('''()=>{const C=ThoughtCore,s=C.fresh();for(let i=0;i<30;i++)C.create(s,'第'+i+'条记录与较长的中文内容，用于验证密集布局。',C.colors[i%5]);localStorage.setItem('thought-collection-v1',JSON.stringify(s))}''')
        page.reload();page.wait_for_function('window.ready===true')
        assert page.locator('.tile').count()==30
        page.locator('#search-toggle').click();page.locator('#search').fill('第17条')
        assert page.locator('.tile').count()==1
        for w in (320,390,1280):
            page.set_viewport_size({'width':w,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.locator('#search').fill('')
        first_id=page.evaluate('window.thoughtApp.state.notes[0].id')
        page.evaluate("() => { window.lockReady=false;navigator.locks.request('thought-collection-write-v1',()=>{window.lockReady=true;return new Promise(resolve=>window.releaseTestLock=resolve)}); }")
        page.wait_for_function('window.lockReady')
        page.locator('.tile').nth(0).dispatch_event('dragstart')
        page.locator('.tile').nth(1).dispatch_event('drop')
        page.locator('.tile').nth(0).dispatch_event('dragend')
        page.evaluate('window.releaseTestLock()')
        page.wait_for_function('id=>window.thoughtApp.state.notes[1].id===id',arg=first_id)
        other=ctx.new_page();other.goto((ROOT/'index.html').as_uri());other.wait_for_function('window.ready===true')
        page.locator('#new-note').click();page.locator('#entry-text').fill('窗口A新增的记录');page.locator('#submit-sheet').click()
        other.locator('#new-note').click();other.locator('#entry-text').fill('窗口B尚未提交的记录');other.locator('#submit-sheet').click()
        assert other.locator('#sheet').is_visible(), 'A stale window must not overwrite a newer saved collection'
        assert other.locator('#entry-text').input_value()=='窗口B尚未提交的记录'
        other.locator('#close-sheet').click();other.locator('#reload-latest').click();other.locator('#new-note').click()
        assert other.locator('#entry-text').input_value()=='窗口B尚未提交的记录'
        other.locator('#submit-sheet').click();page.reload();page.wait_for_function('window.ready===true')
        assert page.evaluate('window.thoughtApp.state.notes.length')==32
        other.locator('[data-action="split"]').click()
        other.locator('[data-child]').nth(0).fill('甲'*700)
        other.locator('[data-child]').nth(1).fill('乙'*700)
        victim=other.evaluate('window.thoughtApp.state.notes.at(-1).id')
        page.evaluate('''id=>{const s=JSON.parse(localStorage.getItem('thought-collection-v1'));ThoughtCore.trash(s,id);ThoughtCore.purge(s,id);localStorage.setItem('thought-collection-v1',JSON.stringify(s))}''',victim)
        other.locator('#submit-sheet').click();other.locator('#close-sheet').click();other.locator('#reload-latest').click()
        assert len(other.locator('textarea[readonly]').input_value())==1402
        other.locator('#submit-sheet').click()
        assert other.evaluate('window.thoughtApp.state.notes.slice(-2).every(n=>n.versions[0].text.length===700)')
        page.reload();page.wait_for_function('window.ready===true')
        other.reload();other.wait_for_function('window.ready===true')
        for tab in (page,other):
            tab.locator('#new-note').click();tab.locator('#entry-text').fill('同时提交测试')
        page.evaluate("() => { window.lockReady=false;navigator.locks.request('thought-collection-write-v1',()=>{window.lockReady=true;return new Promise(resolve=>window.releaseTestLock=resolve)}); }")
        page.wait_for_function('window.lockReady')
        page.evaluate("document.querySelector('#sheet-form').requestSubmit()")
        other.evaluate("document.querySelector('#sheet-form').requestSubmit()")
        page.evaluate('window.releaseTestLock()')
        page.wait_for_function("!document.querySelector('#sheet').open")
        other.wait_for_function("document.querySelector('#form-error').textContent.includes('另一个窗口')")
        assert page.evaluate("JSON.parse(localStorage.getItem('thought-collection-v1')).notes.filter(n=>n.versions[0].text==='同时提交测试').length") == 1
        other.close()
        fixture=page.evaluate('JSON.stringify(ThoughtCore.demo())')
        assert not errors,errors
        ctx.close()
        blocked=browser.new_context(viewport={'width':390,'height':844})
        blocked.set_offline(True)
        blocked.add_init_script("Storage.prototype.setItem=function(){throw new DOMException('blocked','QuotaExceededError')}")
        p=blocked.new_page();p.goto((ROOT/'index.html').as_uri());p.wait_for_function('window.ready===true')
        p.locator('#new-note').click();p.locator('#entry-text').fill('保存失败时也不能丢掉这句话')
        p.locator('#submit-sheet').click()
        assert p.locator('#sheet').is_visible()
        assert p.locator('#entry-text').input_value()=='保存失败时也不能丢掉这句话'
        assert p.evaluate('window.thoughtApp.state.notes.length')==0
        p.locator('#close-sheet').click();p.locator('#session-only').click()
        p.locator('#new-note').click()
        assert p.locator('#entry-text').input_value()=='保存失败时也不能丢掉这句话'
        p.locator('#submit-sheet').click()
        assert p.evaluate('window.thoughtApp.state.notes.length')==1
        blocked.close()
        editctx=browser.new_context(viewport={'width':390,'height':844});editctx.set_offline(True)
        edit=editctx.new_page();edit.goto((ROOT/'index.html').as_uri());edit.wait_for_function('window.ready===true')
        edit.evaluate('(raw)=>localStorage.setItem("thought-collection-v1",raw)',fixture)
        edit.reload();edit.wait_for_function('window.ready===true')
        edit.evaluate("() => { Storage.prototype.setItem=function(){throw new DOMException('blocked','QuotaExceededError')}; }")
        edit.locator('.open-note').first.click();edit.locator('[data-action="addition"]').click()
        edit.locator('#entry-text').fill('保存失败后仍应保留的补充')
        edit.locator('#submit-sheet').click();assert edit.locator('#sheet').is_visible()
        edit.locator('#close-sheet').click();edit.locator('#session-only').click()
        edit.locator('[data-action="addition"]').click()
        assert edit.locator('#entry-text').input_value()=='保存失败后仍应保留的补充'
        edit.locator('#submit-sheet').click()
        assert edit.evaluate('window.thoughtApp.state.notes[0].versions.length')==3
        editctx.close();browser.close()
    result={'browser':'Edge headless','offline':True,'widths':[320,390,1280],'core_flows':['empty/demo isolation including private drafts','append/wording/compare','atomic split','explicit link reason','private PNG export','trash/undo','reload persistence','30 records/search','new and append storage-failure draft retention','two-window stale-write prevention','simultaneous submits serialized by Web Locks','700+700 character split-draft conflict recovery','quick menu preserves home route'],'page_errors':errors,'device_tested':False}
    (ROOT/'browser-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':run()
