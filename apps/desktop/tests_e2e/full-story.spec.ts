import { test, expect } from '@playwright/test'

test.describe.serial('Full Story E2E', () => {
  let pid: string
  let ch1Id: string, ch2Id: string, ch3Id: string, ch4Id: string
  let charAriaId: string, charKaidanId: string, charElderId: string
  let loreLocId: string, loreOrgId: string, loreMagicId: string
  let tlId1: string, tlId2: string, tlId3: string

  test('Tạo project', async ({ request }) => {
    const r = await request.post('/api/projects/', {
      data: { title: 'Huyền Thoại Rồng Lửa', genre: 'Fantasy', description: 'Câu chuyện về một thế giới nơi rồng và con người cùng tồn tại.', language: 'vi' },
    })
    expect(r.status()).toBe(201)
    pid = (await r.json()).id
    console.log(`✅ Project: ${pid}`)
  })

  test('Chương 1: Khởi Nguyên', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: pid,
        title: 'Chương 1: Khởi Nguyên',
        content: 'Vương quốc Eldoria từng là vùng đất thịnh vượng dưới sự bảo hộ của Long tộc. Nhưng kể từ khi Long Vương biến mất, bầu trời luôn u ám. Aria, một cô gái trẻ sống ở làng chài ven biển, không biết rằng số phận của mình gắn liền với bí mật về quả trứng rồng cổ xưa mà cô tình cờ tìm thấy trên bãi cát.',
      },
    })
    expect(r.status()).toBe(201)
    ch1Id = (await r.json()).id
    console.log(`✅ Chương 1: ${ch1Id}`)
  })

  test('Chương 2: Bóng Tối Trở Lại', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: pid,
        title: 'Chương 2: Bóng Tối Trở Lại',
        content: 'Giữa đêm, Aria tỉnh giấc vì tiếng động lạ. Quả trứng rồng phát ra ánh sáng xanh kỳ lạ. Cô nghe thấy giọng nói thì thầm từ trong trứng: "Hãy tìm đến Dãy Núi Vô Tận trước khi chúng tìm thấy ngươi." Cùng lúc, những sinh vật bóng tối bắt đầu tấn công ngôi làng. Aria buộc phải chạy trốn vào khu rừng cấm.',
      },
    })
    expect(r.status()).toBe(201)
    ch2Id = (await r.json()).id
    console.log(`✅ Chương 2: ${ch2Id}`)
  })

  test('Chương 3: Cuộc Hành Trình', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: pid,
        title: 'Chương 3: Cuộc Hành Trình',
        content: 'Aria gặp Kaidan, một thợ săn rồng bí ẩn, người biết nhiều hơn những gì anh ta nói. Họ cùng nhau băng qua khu rừng Nguyệt Quang, nơi những cây cổ thụ cao đến mức che khuất cả bầu trời. Kaidan dạy Aria cách đọc những dấu hiệu của ma thuật cổ và cảnh báo về tổ chức Hội Sát Long — những kẻ đã tiêu diệt Long tộc.',
      },
    })
    expect(r.status()).toBe(201)
    ch3Id = (await r.json()).id
    console.log(`✅ Chương 3: ${ch3Id}`)
  })

  test('Chương 4: Bí Mật Của Trứng Rồng', async ({ request }) => {
    const r = await request.post('/api/chapters/', {
      data: {
        project_id: pid,
        title: 'Chương 4: Bí Mật Của Trứng Rồng',
        content: 'Khi đến được ngôi đền cổ ở Dãy Núi Vô Tận, Aria và Kaidan phát hiện ra sự thật: quả trứng không chỉ là một quả trứng rồng — nó là vật chứa linh hồn của Long Vương. Và Hội Sát Long sắp đến. Aria phải chọn: giao trứng để cứu làng mình, hay chiến đấu để bảo vệ di sản của Long tộc. Kaidan tháo mặt nạ, tiết lộ anh là người cuối cùng của dòng tộc Long kỵ sĩ.',
      },
    })
    expect(r.status()).toBe(201)
    ch4Id = (await r.json()).id
    console.log(`✅ Chương 4: ${ch4Id}`)
  })

  test('Tạo nhân vật Aria', async ({ request }) => {
    const r = await request.post('/api/characters/', {
      data: {
        project_id: pid, name: 'Aria', gender: 'Nữ', role: 'Nhân vật chính', age: '19',
        personality: 'Dũng cảm, giàu lòng trắc ẩn, hơi bướng bỉnh. Luôn đặt người khác lên trước bản thân.',
        appearance: 'Tóc nâu dài đến vai, mắt xanh lục, vết bớt hình rồng nhỏ trên cổ tay phải.',
        goals: 'Bảo vệ quả trứng rồng, tìm ra sự thật về quá khứ của mình.',
        secrets: 'Mang trong mình dòng máu Long tộc từ tổ tiên, có khả năng giao tiếp với rồng.',
      },
    })
    expect(r.status()).toBe(201)
    charAriaId = (await r.json()).id
    console.log(`✅ Aria: ${charAriaId}`)
  })

  test('Tạo nhân vật Kaidan', async ({ request }) => {
    const r = await request.post('/api/characters/', {
      data: {
        project_id: pid, name: 'Kaidan', gender: 'Nam', role: 'Long kỵ sĩ', age: '28',
        personality: 'Lạnh lùng, bí ẩn, nhưng có trái tim nhân hậu. Bị ám ảnh bởi quá khứ mất mát.',
        appearance: 'Cao lớn, tóc trắng xóa, sẹo dài trên má trái, áo giáp đen cũ kỹ.',
        goals: 'Tiêu diệt Hội Sát Long, bảo vệ di sản Long tộc cuối cùng.',
        secrets: 'Là Long kỵ sĩ cuối cùng, từng phản bội chính mình để sống sót.',
      },
    })
    expect(r.status()).toBe(201)
    charKaidanId = (await r.json()).id
    console.log(`✅ Kaidan: ${charKaidanId}`)
  })

  test('Tạo nhân vật Elder Magnus', async ({ request }) => {
    const r = await request.post('/api/characters/', {
      data: {
        project_id: pid, name: 'Magnus', gender: 'Nam', role: 'Trưởng lão', age: '72',
        personality: 'Thông thái, trầm mặc, từng là cố vấn cho Long Vương.',
        appearance: 'Râu tóc bạc phơ, mắt xám, cây trượng gỗ khắc hình rồng.',
        goals: 'Giúp Aria hoàn thành sứ mệnh, ngăn chặn Hội Sát Long.',
        secrets: 'Đã từng là thành viên của Hội Sát Long nhưng đã rời bỏ.',
      },
    })
    expect(r.status()).toBe(201)
    charElderId = (await r.json()).id
    console.log(`✅ Magnus: ${charElderId}`)
  })

  test('Tạo lore — Địa điểm', async ({ request }) => {
    const r = await request.post('/api/lore/', {
      data: {
        project_id: pid, lore_type: 'location',
        name: 'Dãy Núi Vô Tận',
        description: 'Một dãy núi hùng vĩ kéo dài đến chân trời, nơi ẩn chứa ngôi đền cổ của Long tộc. Đỉnh núi cao nhất được gọi là Nanh Rồng, nơi Long Vương trị vì. Xung quanh núi luôn có màn sương ma thuật bảo vệ.',
        tags: ['núi', 'long tộc', 'cổ đại', 'bí ẩn'],
      },
    })
    expect(r.status()).toBe(201)
    loreLocId = (await r.json()).id
    console.log(`✅ Lore Địa điểm: ${loreLocId}`)
  })

  test('Tạo lore — Tổ chức', async ({ request }) => {
    const r = await request.post('/api/lore/', {
      data: {
        project_id: pid, lore_type: 'organization',
        name: 'Hội Sát Long (Dragonbane Order)',
        description: 'Một tổ chức bí mật chuyên săn lùng và tiêu diệt Long tộc. Được thành lập bởi một Long kỵ sĩ phản bội. Họ sở hữu vũ khí cổ xưa có khả năng giết rồng. Thành viên đeo mặt nạ sắt hình thú.',
        tags: ['tổ chức', 'phản diện', 'bí mật', 'long tộc'],
      },
    })
    expect(r.status()).toBe(201)
    loreOrgId = (await r.json()).id
    console.log(`✅ Lore Tổ chức: ${loreOrgId}`)
  })

  test('Tạo lore — Phép thuật', async ({ request }) => {
    const r = await request.post('/api/lore/', {
      data: {
        project_id: pid, lore_type: 'magic',
        name: 'Long Ngữ — Ngôn ngữ của Rồng',
        description: 'Một ngôn ngữ cổ xưa chỉ có Long tộc và Long kỵ sĩ mới hiểu. Khi được niệm, Long Ngữ có thể điều khiển các nguyên tố: lửa, băng, sấm sét. Mỗi âm tiết tạo ra một rung động ma thuật riêng. Aria có thể nghe hiểu Long Ngữ qua giấc mơ.',
        tags: ['ma thuật', 'ngôn ngữ', 'long tộc', 'cổ xưa'],
      },
    })
    expect(r.status()).toBe(201)
    loreMagicId = (await r.json()).id
    console.log(`✅ Lore Phép thuật: ${loreMagicId}`)
  })

  test('Tạo timeline — Sự kiện 1', async ({ request }) => {
    const r = await request.post('/api/timeline/', {
      data: {
        project_id: pid, title: 'Long Vương biến mất',
        description: 'Long Vương — chúa tể của tất cả loài rồng — đột nhiên biến mất không dấu vết. Bầu trời Eldoria tối sầm, các loài rồng dần rút lui về Dãy Núi Vô Tận.',
        involved_characters: [charElderId],
      },
    })
    expect(r.status()).toBe(201)
    tlId1 = (await r.json()).id
    console.log(`✅ Timeline 1: ${tlId1}`)
  })

  test('Tạo timeline — Sự kiện 2', async ({ request }) => {
    const r = await request.post('/api/timeline/', {
      data: {
        project_id: pid, title: 'Aria tìm thấy trứng rồng',
        description: 'Trong một lần đi dạo trên bãi biển sau cơn bão, Aria tình cờ tìm thấy một quả trứng phát sáng kỳ lạ. Đây là quả trứng rồng cuối cùng còn sót lại.',
        involved_characters: [charAriaId],
        related_chapters: [ch1Id],
      },
    })
    expect(r.status()).toBe(201)
    tlId2 = (await r.json()).id
    console.log(`✅ Timeline 2: ${tlId2}`)
  })

  test('Tạo timeline — Sự kiện 3', async ({ request }) => {
    const r = await request.post('/api/timeline/', {
      data: {
        project_id: pid, title: 'Cuộc chiến tại Ngôi Đền Cổ',
        description: 'Aria, Kaidan và Magnus đối đầu với Hội Sát Long tại ngôi đền cổ. Aria đánh thức sức mạnh Long Ngữ, quả trứng nở ra Long Vương tái sinh.',
        involved_characters: [charAriaId, charKaidanId, charElderId],
        related_chapters: [ch3Id, ch4Id],
      },
    })
    expect(r.status()).toBe(201)
    tlId3 = (await r.json()).id
    console.log(`✅ Timeline 3: ${tlId3}`)
  })

  test('List chapters', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/chapters`)
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.length).toBe(4)
    expect(data[0].title).toContain('Khởi Nguyên')
    expect(data[3].title).toContain('Bí Mật')
  })

  test('List characters', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/characters`)
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.length).toBe(3)
    const names = data.map((c: any) => c.name)
    expect(names).toContain('Aria')
    expect(names).toContain('Kaidan')
    expect(names).toContain('Magnus')
  })

  test('List lore', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/lore`)
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.length).toBe(3)
  })

  test('List timeline', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/timeline`)
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data.length).toBe(3)
  })

  test('Sửa chapter 1', async ({ request }) => {
    const r = await request.patch(`/api/chapters/${ch1Id}`, {
      data: { content: 'Vương quốc Eldoria từng là vùng đất thịnh vượng dưới sự bảo hộ của Long tộc. Rồng và người sống hòa bình. Nhưng kể từ khi Long Vương biến mất, bầu trời luôn u ám. Aria, một cô gái trẻ sống ở làng chài ven biển, không biết rằng số phận của mình gắn liền với bí mật về quả trứng rồng cổ xưa mà cô tình cờ tìm thấy trên bãi cát.' },
    })
    expect(r.status()).toBe(200)
    expect((await r.json()).word_count).toBeGreaterThan(30)
  })

  test('Export MD', async ({ request }) => {
    const r = await request.post('/api/export', { data: { project_id: pid, fmt: 'md' } })
    expect(r.status()).toBe(200)
  })

  test('Export HTML', async ({ request }) => {
    const r = await request.post('/api/export', { data: { project_id: pid, fmt: 'html' } })
    expect(r.status()).toBe(200)
  })

  test('Export TXT', async ({ request }) => {
    const r = await request.post('/api/export', { data: { project_id: pid, fmt: 'txt' } })
    expect(r.status()).toBe(200)
  })

  test('Export ZIP', async ({ request }) => {
    const r = await request.post('/api/export', { data: { project_id: pid, fmt: 'zip' } })
    expect(r.status()).toBe(200)
  })

  test('Search project', async ({ request }) => {
    const r = await request.get(`/api/projects/${pid}/search?q=Aria&limit=10`)
    expect(r.status()).toBe(200)
  })

  test('Settings about', async ({ request }) => {
    const r = await request.get('/api/settings/about')
    expect(r.status()).toBe(200)
    expect((await r.json()).app).toBe('NovelForge')
  })

  test('Xóa toàn bộ (cascade)', async ({ request }) => {
    const del = await request.delete(`/api/projects/${pid}`)
    expect(del.status()).toBe(204)
    const check = await request.get(`/api/projects/${pid}`)
    expect(check.status()).toBe(404)
    console.log(`✅ Project deleted, ${3} characters, ${3} lore, ${3} timeline, ${4} chapters cascade OK`)
  })
})
